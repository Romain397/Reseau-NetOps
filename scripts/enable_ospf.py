"""Activer OSPF après réussite des tests de base sur LAB."""
import subprocess
import sys

from prepare import ROOT, load_model


def main():
    subprocess.run([sys.executable, str(ROOT / 'scripts/prepare.py'), '--check'], check=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/verify.py')], check=True)
    fabric, *_ = load_model()
    for name in [*fabric['core'], *fabric['pes']]:
        lines = (ROOT / f'configs/ospf/{name}.cli').read_text(encoding='utf-8').splitlines()
        commands = '\n'.join(line for line in lines if not line.startswith('!'))
        result = subprocess.run(['docker', 'exec', f"clab-{fabric['lab_name']}-{name}",
                                 'Cli', '-p', '15', '-c', commands],
                                text=True, capture_output=True, timeout=60)
        print(name, result.stdout, result.stderr, flush=True)
        if result.returncode or '%' in result.stdout or '%' in result.stderr:
            raise SystemExit(f'Configuration interrompue sur {name} ; examiner les sorties.')
    print('OSPF configuré. Attendre la convergence puis lancer python3 scripts/verify.py --ospf.')


if __name__ == '__main__':
    main()
