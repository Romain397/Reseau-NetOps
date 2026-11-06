#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
python3 scripts/prepare.py --check
python3 - <<'PY'
import ipaddress
import json
import subprocess
from pathlib import Path
import yaml
fabric = yaml.safe_load(Path('data/fabric.yml').read_text())
planned = ipaddress.ip_network(fabric['management_subnet'])
for image in (fabric['ceos_image'], fabric['host_image']):
    subprocess.run(['docker', 'image', 'inspect', image], check=True, stdout=subprocess.DEVNULL)
ids = subprocess.check_output(['docker', 'network', 'ls', '-q'], text=True).split()
networks = json.loads(subprocess.check_output(['docker', 'network', 'inspect', *ids], text=True))
for network in networks:
    for config in network.get('IPAM', {}).get('Config') or []:
        subnet = ipaddress.ip_network(config['Subnet'])
        if subnet.version != 4 or not planned.overlaps(subnet):
            continue
        if network['Name'] != fabric['lab_name'] + '-mgmt' or subnet != planned:
            raise SystemExit('Conflit de management avec le réseau Docker ' + network['Name'])
routes = json.loads(subprocess.check_output(['ip', '-j', '-4', 'route'], text=True))
for route in routes:
    if route.get('dst', 'default') == 'default':
        continue
    subnet = ipaddress.ip_network(route['dst'])
    if planned.overlaps(subnet) and subnet != planned:
        raise SystemExit('Conflit de management avec une route de LAB : ' + str(subnet))
print('Images présentes ; réseau de management sans conflit détecté.')
PY
mkdir -p reports
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
sudo -n containerlab deploy -t topology.yml --max-workers 2 2>&1 | tee "reports/deploy-${stamp}.log"
echo 'Déploiement terminé. Lancer python3 scripts/verify.py après le démarrage EOS.'
