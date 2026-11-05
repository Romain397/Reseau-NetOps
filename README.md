# Reseau-NetOps

Préparation de la journée projet, limitée aux six étapes de la feuille de route.

L'architecture retenue comprend **13 équipements** : quatre hosts, quatre CE,
trois PE et deux P. **PE-PAR est partagé par les deux filiales**.

## Documents et brouillons

| Élément | Étapes concernées | État |
|---|---|---|
| [Feuille de route](docs/feuille-de-route.md) | 1 à 6 | Analyse, conception et préparation |
| [Variables et adressage](data/fabric.yml) | 3 et 5 | Proposition à valider |
| [Inventaire Ansible](inventory/hosts.yml) | 5 | Brouillon des 13 équipements |
| [Paramètres eAPI](inventory/group_vars/eos.yml) | 5 | Préparation HTTPS/443, sans identifiants |
| [Template Jinja2](templates/eos.cfg.j2) | 5 | Squelette incomplet, non rendu |

Le dépôt contient uniquement des documents et des fichiers préparatoires.
Aucune configuration finale, topologie de déploiement, automatisation de
déploiement ou supervision active n'est fournie. Aucune installation de
dépendances ne fait partie de cette préparation.

Les adresses constituent des choix proposés. Les résultats des futurs tests
restent à recueillir sur le laboratoire fourni. Les fichiers de cours et le
manuel EOS restent hors du dépôt public.
