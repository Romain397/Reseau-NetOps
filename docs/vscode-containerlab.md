# Utiliser Containerlab depuis VS Code sur le PC Windows

## Configuration réalisée le 6 novembre 2026

- Extension locale Containerlab : `srl-labs.vscode-containerlab` 0.26.3.
- Extension locale Remote SSH : `ms-vscode-remote.remote-ssh` 0.128.0.
- Hôte SSH `netops-lab` : `NetOps@10.108.2.65`.
- Clé dédiée dans le profil Windows : `~/.ssh/id_ed25519_netops_lab`.
  Le fichier privé et les mots de passe ne sont pas dans le dépôt.
- VS Code Server et Containerlab 0.26.3 installés sur LAB ; dépendances
  YAML et Draw.io installées côté distant.
- Dossier distant : `/home/NetOps/Reseau-NetOps`.
- Exécutable distant de l'extension : `/usr/bin/containerlab`.
- Action d'attachement configurée : `Cli` pour les cEOS, `sh` pour les hosts.

La connexion SSH par clé et la lecture du laboratoire ont été testées.
Dans la fenêtre **`Reseau-NetOps [SSH: netops-lab]`**, l'explorateur Containerlab
affiche le laboratoire **`netops (NetOps)`** et ses **13 nœuds running**.

## Ouvrir la bonne fenêtre

1. Connecter le VPN.
2. Dans VS Code, ouvrir la palette avec `Ctrl+Maj+P`.
3. Choisir **Remote-SSH: Connect to Host...**, puis **netops-lab**.
4. Ouvrir `/home/NetOps/Reseau-NetOps` et cliquer sur l'icône Containerlab.
5. Dans **Running Labs**, développer **netops (NetOps)**.

La barre d'état doit afficher **SSH: netops-lab**. Une fenêtre ouverte sur
le dossier Windows exécute les extensions locales et ne contrôle pas le
Docker de LAB. Il n'est pas nécessaire d'installer Containerlab ou les neuf
routeurs sur Windows pour administrer ce laboratoire.

Le fichier déployé demeure `topology.yml`. L'extension sait découvrir le
laboratoire en cours même si ce fichier ne porte pas le suffixe `.clab.yml`.
Les boutons de titre de l'éditeur et la découverte des topologies non
déployées utilisent, eux, les suffixes `.clab.yml` et `.clab.yaml`.
Un fichier généré sous `clab-netops/` peut donc aussi apparaître dans la
section des laboratoires non déployés : utiliser l'entrée **Running Labs**
pour administrer la topologie déjà active.

L'accès aux CLI passe par `docker exec` sur LAB. Les cEOS ne possèdent pas
encore de compte SSH/eAPI distant provisionné pour le projet. Les commandes
Destroy/Redeploy peuvent interrompre le laboratoire et ne sont pas nécessaires
pour consulter les équipements ou la topologie.

La version Containerlab actuellement relevée sur LAB est **0.82.0**, après
la mise à jour observée dans VS Code. La version initiale était 0.79.0.
La campagne réseau a été rejouée à partir de **14:30:27 CET** :
**91/91 contrôles réussis**, dont les sept adjacences OSPF et les pings entre
loopbacks. Le [bilan JSON](tests/ospf-after-vscode-summary.json) est versionné.

Références : [extension Containerlab et fonctionnement distant](https://containerlab.dev/manual/gui/vsc-extension/),
[VS Code Remote SSH](https://code.visualstudio.com/docs/remote/ssh).
