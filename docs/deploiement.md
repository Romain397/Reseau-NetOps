# Déployer la phase de base sur LAB

## Répartition et arborescence

Copie de travail Git sur TOOLS, copie d'exécution sur LAB, sous
`/home/NetOps/Reseau-NetOps`. Les deux VM ne partagent pas automatiquement
leurs fichiers. Transférer des révisions identifiées avec Git et éviter des
modifications simultanées divergentes.

```text
Reseau-NetOps/
├── topology.yml
├── data/fabric.yml
├── configs/base/       # 9 configurations de démarrage
├── configs/ospf/       # 5 fragments CLI
├── configs/snapshots/  # Configurations actives relevées après validation
├── templates/eos.cfg.j2
├── inventory/          # Préparation Ansible ; eAPI non activé
├── scripts/            # prepare, deploy, verify, enable_ospf
├── docs/               # Procédure, câblage, journal et conception
└── reports/            # Sorties de tests et déploiement, non versionnées
```

## Vérifications et premier démarrage

Sur LAB, conserver EdgeShark/Ghostwire. Sur TOOLS, conserver l'environnement
Nautobot et ses dépendances.

```sh
cd /home/NetOps/Reseau-NetOps
ip -4 route
docker network ls
docker ps -a
free -h
df -h /
python3 scripts/prepare.py --check
bash scripts/deploy.sh
```

Le script vérifie les deux images et l'absence de conflit du réseau de
management avec les réseaux Docker et routes de LAB. Il limite à deux les
tâches simultanées. Il n'installe pas de logiciels et ne détruit pas de
conteneurs. `requirements.txt` décrit les dépendances pour un autre poste.

Management : `172.31.255.0/24`, réseau Docker `netops-mgmt`, passerelle `.1`.
L'accès routé depuis TOOLS reste à concevoir avec filtrage, authentification
et certificats. L'administration depuis LAB suffit pour cette journée.

Voir [cablage.md](cablage.md) pour les 15 liens. `ethN` dans Containerlab
correspond à `EthernetN` dans EOS. Le management utilise eth0/Management0.
Les hosts conservent leur route de management sur eth0 et des routes
spécifiques vers les autres LAN clients via leur CE sur eth1.

## Contrôler la base avant OSPF

```sh
sudo -n containerlab inspect -t topology.yml
python3 scripts/verify.py
```

Attendu : 13 conteneurs running, IP attendues sur interfaces et neuf loopbacks,
management dans MGMT, **30 pings de voisinage réussis** (15 liens dans les deux
sens). Le test doit sortir avec le code 0. Chaque exécution écrit `summary.json`
et `commands.log` dans un répertoire horodaté de `reports/`.

Diagnostic, en adaptant les noms :

```sh
docker logs --tail 100 clab-netops-p1
docker exec clab-netops-p1 Cli -p 15 -c 'show ip interface brief'
docker exec clab-netops-p1 Cli -p 15 -c 'show interfaces status'
docker exec clab-netops-host-a-par ip -br address
docker exec clab-netops-host-a-par ip route
```

Un conteneur running ne prouve pas que le CLI EOS est prêt. Attendre la fin
du démarrage avant de relancer un contrôle en échec.

## Activer OSPF area 0

```sh
python3 scripts/enable_ospf.py
# Attendre la convergence, puis :
python3 scripts/verify.py --ospf
```

OSPF utilise les sept liens P-PE/P-P et cinq loopbacks du backbone.
Les liens sont point-à-point et les loopbacks passives. Aucun OSPF sur les
CE, les LAN clients ou le management.

| Routeur | Router ID | Voisins FULL attendus |
|---|---|---:|
| p1 | 10.255.0.1 | 4 |
| p2 | 10.255.0.2 | 4 |
| pe-par | 10.255.0.11 | 2 |
| pe-avi | 10.255.0.12 | 2 |
| pe-bdx | 10.255.0.13 | 2 |

Il y a sept adjacences, vues depuis leurs deux extrémités. Le contrôle exige
les Router ID attendus en FULL, les routes des quatre loopbacks distantes
et les 20 pings entre loopbacks avec source Loopback0. Il rejoue les tests de base.

Les hosts ne communiquent pas encore entre sites. Cette connectivité viendra
avec les VRF clientes, LDP et MP-BGP/eBGP. Un échec intersite à ce stade ne
permet pas de conclure sur l'isolation finale de la L3VPN.

## Conservation et reprise

Les fragments OSPF exécutent `write memory`. Le laboratoire existant réutilise
ses configurations persistées. Un laboratoire neuf charge `configs/base/` :
rejouer ensuite l'activation OSPF. Un nouveau rendu des fichiers ne modifie
pas les routeurs déjà démarrés.

Après validation, `python3 scripts/snapshot.py` exporte les neuf configurations
actives dans `configs/snapshots/`. Le script refuse l'export si un élément
potentiellement sensible est détecté. Ces fichiers sont des preuves de l'état
relevé ; `topology.yml` utilise toujours les configurations de base.

Ne pas utiliser `--reconfigure` pour un simple contrôle : cela peut écraser
les configurations. Ne pas ajouter `clab-*` à Git : ces répertoires incluent
des certificats et d'autres artefacts. Ne pas utiliser `docker system prune`
pour remettre ce projet à zéro.

Références : [configuration cEOS et interfaces](https://containerlab.dev/manual/kinds/ceos/),
[management Containerlab](https://containerlab.dev/manual/network/),
[commandes OSPF EOS](https://www.arista.com/en/um-eos/eos-open-shortest-path-first-version-2).
