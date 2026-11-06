# Reseau-NetOps

Phase du jour : déployer le laboratoire, configurer les interfaces et les loopbacks,
puis activer OSPF area 0 après réussite des tests de base.

**État validé le 6 novembre 2026 : déployé sur LAB, 91/91 contrôles réussis.**
Voir [le journal et les preuves](docs/journal-2026-11-06.md).

L'architecture retenue comprend **13 équipements** : quatre hosts, quatre CE,
trois PE et deux P. **PE-PAR est partagé par les deux filiales**.

`toolsG2` (`10.108.2.29/24`) accueille la copie Git et la documentation.
`labG2` (`10.108.2.65/24`) héberge Containerlab, les 13 conteneurs, les tests
et le premier contrôleur Ansible. L'accès routé de TOOLS au management des
conteneurs reste une étape ultérieure.

## Fichiers du projet

| Élément | Étapes concernées | État |
|---|---|---|
| [Topologie Containerlab](topology.yml) | Déploiement | 13 nœuds et 15 liens |
| [Variables et adressage](data/fabric.yml) | Conception | Source des artefacts générés |
| [Câblage](docs/cablage.md) | Contrôle | Interfaces et IP des 15 liens |
| [Procédure LAB](docs/deploiement.md) | Exécution | Commandes et résultats attendus |
| [Journal du jour](docs/journal-2026-11-06.md) | Preuves | Résultats réellement recueillis |
| [Environnement des deux VM](docs/environnement-vm.md) | Infrastructure | État fourni et contrôles SSH |
| [Containerlab dans VS Code](docs/vscode-containerlab.md) | Administration | Connexion distante à LAB depuis Windows |
| [Inventaire Ansible](inventory/hosts.yml) | Phase future | Deux VM et 13 équipements |
| [Template Jinja2](templates/eos.cfg.j2) | Base | Interfaces, management et loopbacks |
| [Feuille de route](docs/feuille-de-route.md) | Projet complet | Conception L3VPN et étapes futures |

## Exécution sur LAB

Depuis `/home/NetOps/Reseau-NetOps`, avec Python, PyYAML et Jinja2 disponibles :

```sh
python3 scripts/prepare.py --check
bash scripts/deploy.sh
python3 scripts/verify.py
python3 scripts/enable_ospf.py
# Après convergence OSPF :
python3 scripts/verify.py --ospf
```

`enable_ospf.py` exige la réussite des tests de base avant de modifier les P/PE.
`configs/base/` contient les neuf configurations de démarrage ; `configs/ospf/`
contient les commandes pour les cinq routeurs du backbone.

Les configurations de base n'activent aucun service d'administration distant.
Accès immédiat depuis LAB : `docker exec -it clab-netops-p1 Cli`.
La VRF MGMT sépare le management Docker des données. Les VRF clientes,
LDP, MP-BGP VPNv4, eBGP, l'automatisation Ansible et la supervision restent
les prochaines étapes. Les hosts ne communiquent pas encore entre sites.

Modifier `data/fabric.yml`, puis lancer `python3 scripts/prepare.py` pour
régénérer les fichiers. Un rendu ne modifie pas les routeurs en fonctionnement.
Les sorties brutes sont dans `reports/`, ignoré par Git ; versionner un bilan
sans secrets dans `docs/`. Les mots de passe et images cEOS restent hors du dépôt.

Les IP des deux VM proviennent des sorties `ip a` de l'utilisateur et sont
dynamiques. Les IP des 13 équipements restent proposées. L'inventaire
comprend donc 15 entrées : deux VM d'infrastructure et 13 équipements réseau.
