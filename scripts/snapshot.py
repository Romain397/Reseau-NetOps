"""Exporter les configurations EOS ; refuser une exportation contenant des secrets."""
import re
import subprocess

from prepare import ROOT, load_model


def main():
    fabric, routers, *_ = load_model()
    snapshots = {}
    for name in routers:
        result = subprocess.run(['docker', 'exec', f"clab-{fabric['lab_name']}-{name}",
                                 'Cli', '-p', '15', '-c', 'show running-config'],
                                text=True, capture_output=True, check=True, timeout=45)
        text = result.stdout
        if '%' in text or not re.search(r'^hostname ' + re.escape(name) + r'$', text, re.M):
            raise SystemExit(f'Configuration invalide ou CLI indisponible : {name}')
        if re.search(r'(?im)^.*(?:username|secret|password|private.key|community).*$' , text):
            raise SystemExit(f'Export refusé : élément potentiellement sensible sur {name}.')
        snapshots[name] = '\n'.join(line for line in text.splitlines()
                                     if not line.startswith('> ')) + '\n'
    target = ROOT / 'configs/snapshots'
    target.mkdir(parents=True, exist_ok=True)
    for name, text in snapshots.items():
        (target / f'{name}.cfg').write_text(text, encoding='utf-8')
    print(f'{len(snapshots)} configurations exportées sans identifiants dans {target}')


if __name__ == '__main__':
    main()
