"""Tests de lecture seule à lancer sur LAB ; échec => code de sortie non nul."""
import argparse
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import re
import subprocess

from prepare import ROOT, load_model, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ospf', action='store_true')
    args = parser.parse_args()
    model = load_model()
    validate(*model)
    fabric, routers, hosts, links = model
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    report_dir = ROOT / 'reports' / stamp
    report_dir.mkdir(parents=True, exist_ok=True)
    failures, results, logs = [], [], []

    def run(label, command, predicate=None):
        result = subprocess.run(command, text=True, capture_output=True, timeout=45)
        text = result.stdout + result.stderr
        logs.append(f'$ {command!r}\n{text}')
        ok = result.returncode == 0 and (predicate(text) if predicate else True)
        results.append(dict(test=label, ok=bool(ok)))
        print(('OK ' if ok else 'ECHEC ') + label, flush=True)
        if not ok:
            failures.append(label)
        return text

    def container(name):
        return f"clab-{fabric['lab_name']}-{name}"

    def cli(name, command):
        return ['docker', 'exec', container(name), 'Cli', '-p', '15', '-c', command]

    def zero_loss(text):
        return bool(re.search(r'(?<![\d.])0(?:\.0+)?% packet loss', text))

    for name in {**routers, **hosts}:
        run(f'{name} running', ['docker', 'inspect', '--format', '{{.State.Running}}',
                                 container(name)], lambda text: text.strip() == 'true')
    for name, node in routers.items():
        run(f'{name} interfaces/loopback', cli(name, 'show ip interface brief'),
            lambda text, node=node: all(address in text for address in
                [node['loopback']] + [i['address'].split('/')[0] for i in node['interfaces']]))
        run(f'{name} management', cli(name, 'show running-config interfaces Management0'),
            lambda text, node=node: node['management'] in text and 'vrf MGMT' in text)
    for link in links:
        for index, endpoint in enumerate(link['endpoints']):
            name, interface = endpoint.split(':')
            peer = link['endpoints'][1-index]
            target = str(ipaddress.ip_interface(link['addresses'][1-index]).ip)
            if name in routers:
                command = cli(name, f'ping {target} source {interface} repeat 3')
            else:
                command = ['docker', 'exec', container(name), 'ping', '-I', interface,
                           '-c', '3', '-W', '2', target]
            run(f'{endpoint} -> {peer}', command, zero_loss)
    if args.ospf:
        backbone = {**fabric['core'], **fabric['pes']}
        for name, node in backbone.items():
            neighbors = {routers[peer.split(':')[0]]['loopback']
                         for link in fabric['backbone']
                         for index, endpoint in enumerate(link['endpoints'])
                         if endpoint.split(':')[0] == name
                         for peer in [link['endpoints'][1-index]]}

            def full_neighbors(text, expected=neighbors):
                rows = [line.split() for line in text.splitlines() if 'FULL' in line.upper()]
                return {row[0] for row in rows} == expected

            run(f'{name} OSPF voisins FULL', cli(name, 'show ip ospf neighbor'), full_neighbors)
            run(f'{name} routes OSPF', cli(name, 'show ip route ospf'),
                lambda text, name=name: all(other['loopback'] in text
                    for other_name, other in backbone.items() if other_name != name))
            for peer, other in backbone.items():
                if peer != name:
                    run(f'{name} Loopback0 -> {peer}',
                        cli(name, f"ping {other['loopback']} source Loopback0 repeat 3"), zero_loss)
    summary = dict(timestamp_utc=stamp, phase='ospf' if args.ospf else 'base',
                   passed=len(results)-len(failures), total=len(results), failures=failures,
                   results=results)
    (report_dir / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (report_dir / 'commands.log').write_text('\n\n'.join(logs), encoding='utf-8')
    print(f"Résultat : {summary['passed']}/{len(results)} ; preuves : {report_dir}")
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
