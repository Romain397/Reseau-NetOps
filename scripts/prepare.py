"""Générer ou contrôler les fichiers de base sans joindre les VM."""
import argparse
import ipaddress as ip
import re
from pathlib import Path

import yaml
from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_model():
    fabric = yaml.safe_load((ROOT / 'data/fabric.yml').read_text(encoding='utf-8'))
    routers, hosts, links = {}, {}, []
    for section in ('core', 'pes'):
        for name, values in fabric[section].items():
            routers[name] = dict(values, name=name, interfaces=[])
    for site in fabric['sites']:
        ce, host = 'ce-' + site['id'], 'host-' + site['id']
        prefix = ip.ip_network(site['lan']).prefixlen
        routers[ce] = dict(name=ce, loopback=site['ce_loopback'],
                          management=site['ce_management'], interfaces=[])
        hosts[host] = dict(management=site['host_management'], gateway=site['gateway'],
                          address=f"{site['host_ip']}/{prefix}")
        links.append(dict(endpoints=[f"{site['pe']}:{site['pe_interface']}", f'{ce}:Ethernet1'],
                          addresses=site['pe_ce'], category='access'))
        links.append(dict(endpoints=[f'{ce}:Ethernet2', f'{host}:eth1'],
                          addresses=[f"{site['gateway']}/{prefix}", hosts[host]['address']],
                          category='lan'))
    links += [dict(link, category='backbone') for link in fabric['backbone']]
    for link in links:
        for index, endpoint in enumerate(link['endpoints']):
            name, interface = endpoint.split(':')
            if name in routers:
                routers[name]['interfaces'].append(dict(name=interface,
                    address=link['addresses'][index], peer=link['endpoints'][1-index]))
    return fabric, routers, hosts, links


def validate(fabric, routers, hosts, links):
    require(len(routers) == 9 and len(hosts) == 4 and len(links) == 15,
            'Attendu : 9 cEOS, 4 hosts et 15 liens')
    require(len(fabric['core']) == 2 and len(fabric['pes']) == 3 and
            len(fabric['sites']) == 4, 'Répartition P/PE/CE incorrecte')
    nodes = {**routers, **hosts}
    require(len(nodes) == 13, 'Noms de nœuds dupliqués')
    management = ip.ip_network(fabric['management_subnet'])
    gateway = ip.ip_address(fabric['management_gateway'])
    require(gateway == management.network_address + 1, 'Passerelle Docker attendue en .1')
    seen_ips, networks = {gateway}, [management]
    for name, node in nodes.items():
        require(re.fullmatch(r'[a-z0-9-]+', name), f'Nom invalide : {name}')
        address = ip.ip_address(node['management'])
        require(address in management and address not in seen_ips and
                address not in (management.network_address, management.broadcast_address),
                f'IP management incorrecte ou dupliquée : {name}')
        seen_ips.add(address)
    loopbacks = [ip.ip_address(node['loopback']) for node in routers.values()]
    require(len(set(loopbacks)) == 9, 'Loopbacks dupliquées')
    seen_endpoints = set()
    graph = {name: set() for name in nodes}
    for link in links:
        addresses = [ip.ip_interface(address) for address in link['addresses']]
        network = addresses[0].network
        require(network == addresses[1].network, f'Sous-réseaux différents : {link}')
        require(addresses[0].ip != addresses[1].ip, f'IP identiques : {link}')
        require(all(a.ip not in (network.network_address, network.broadcast_address)
                    for a in addresses), f'IP réseau ou broadcast : {link}')
        require(all(not network.overlaps(other) for other in networks),
                f'Chevauchement : {network}')
        networks.append(network)
        for endpoint in link['endpoints']:
            name, interface = endpoint.split(':')
            require(name in nodes and endpoint not in seen_endpoints,
                    f'Extrémité inconnue ou réutilisée : {endpoint}')
            require(re.fullmatch(r'Ethernet[1-9][0-9]*' if name in routers else r'eth1',
                                 interface), f'Interface incorrecte : {endpoint}')
            seen_endpoints.add(endpoint)
        left, right = [endpoint.split(':')[0] for endpoint in link['endpoints']]
        require(left != right, 'Lien vers soi-même')
        graph[left].add(right)
        graph[right].add(left)
    require(all(not ip.ip_network(f'{address}/32').overlaps(network)
                for address in loopbacks for network in networks), 'Loopback dans un lien/management')
    reached, pending = set(), [next(iter(nodes))]
    while pending:
        node = pending.pop()
        if node not in reached:
            reached.add(node)
            pending.extend(graph[node] - reached)
    require(reached == set(nodes), 'Topologie non connexe')
    inventory = yaml.safe_load((ROOT / 'inventory/hosts.yml').read_text(encoding='utf-8'))
    inventory_hosts = {}

    def collect(group):
        inventory_hosts.update(group.get('hosts', {}))
        for child in group.get('children', {}).values():
            collect(child)

    collect(inventory['all'])
    require(set(inventory_hosts) == set(nodes) | set(fabric['environment']['vms']),
            'Noms incohérents dans l’inventaire')
    for name, node in nodes.items():
        require(inventory_hosts[name]['ansible_host'] == node['management'],
                f'Inventaire incohérent : {name}')


def artifacts(fabric, routers, hosts, links):
    template = Environment(undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True,
                           keep_trailing_newline=True).from_string(
                               (ROOT / 'templates/eos.cfg.j2').read_text(encoding='utf-8'))
    nodes, output = {}, {}
    for name, node in routers.items():
        output[f'configs/base/{name}.cfg'] = template.render(**node,
            management_prefix=ip.ip_network(fabric['management_subnet']).prefixlen,
            management_gateway=fabric['management_gateway'])
        nodes[name] = dict(kind='arista_ceos', **{'mgmt-ipv4': node['management'],
                           'startup-config': f'configs/base/{name}.cfg'})
    for name, host in hosts.items():
        # Garder la route de management sur eth0 ; acheminer les LAN clients via eth1.
        commands = ['ip link set dev eth1 up',
                    f"ip address replace {host['address']} dev eth1"]
        commands += [f"ip route replace {site['lan']} via {host['gateway']} dev eth1"
                     for site in fabric['sites'] if host['gateway'] != site['gateway']]
        nodes[name] = dict(kind='linux', **{'mgmt-ipv4': host['management'], 'exec': commands})
    topology = dict(name=fabric['lab_name'], mgmt={
        'network': f"{fabric['lab_name']}-mgmt", 'ipv4-subnet': fabric['management_subnet']},
        topology=dict(kinds={'arista_ceos': {'image': fabric['ceos_image']},
                             'linux': {'image': fabric['host_image']}}, nodes=nodes,
                      links=[{'endpoints': [e.replace(':Ethernet', ':eth')
                               for e in link['endpoints']]} for link in links]))
    output['topology.yml'] = '# Généré par scripts/prepare.py ; modifier data/fabric.yml.\n' + yaml.safe_dump(
        topology, sort_keys=False, allow_unicode=True)
    for name, node in routers.items():
        if name not in fabric['core'] and name not in fabric['pes']:
            continue
        interfaces = [endpoint.split(':')[1] for link in fabric['backbone']
                      for endpoint in link['endpoints'] if endpoint.split(':')[0] == name]
        lines = ['! À appliquer après les tests de base.', 'configure terminal']
        for interface in interfaces:
            lines += [f'interface {interface}', '   ip ospf network point-to-point',
                      '   ip ospf area 0.0.0.0', 'exit']
        lines += ['interface Loopback0', '   ip ospf area 0.0.0.0', 'exit',
                  'router ospf 1', f"   router-id {node['loopback']}",
                  '   passive-interface default']
        lines += [f'   no passive-interface {interface}' for interface in interfaces]
        lines += ['   max-lsa 12000', 'end', 'write memory']
        output[f'configs/ospf/{name}.cli'] = '\n'.join(lines) + '\n'
    rows = ['# Câblage et adressage', '',
            'Généré depuis `data/fabric.yml`. `ethN` dans Containerlab correspond à',
            '`EthernetN` dans EOS. Le management utilise `eth0` / `Management0`.', '',
            '| Lien | Extrémité A | IPv4 A | Extrémité B | IPv4 B | Usage |',
            '|---:|---|---|---|---|---|']
    for index, link in enumerate(links, 1):
        rows.append(f"| {index} | {link['endpoints'][0]} | {link['addresses'][0]} | "
                    f"{link['endpoints'][1]} | {link['addresses'][1]} | {link['category']} |")
    output['docs/cablage.md'] = '\n'.join(rows) + '\n'
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Vérifier sans réécrire')
    args = parser.parse_args()
    model = load_model()
    validate(*model)
    for relative, content in artifacts(*model).items():
        path = ROOT / relative
        if args.check:
            require(path.exists() and path.read_text(encoding='utf-8') == content,
                    f'Fichier absent ou périmé : {relative} ; exécuter scripts/prepare.py')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
    print('OK : 13 nœuds (9 cEOS + 4 hosts), 15 liens, IP, inventaire et fichiers cohérents.')


if __name__ == '__main__':
    main()
