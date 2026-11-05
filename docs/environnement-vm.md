# Préparation de l'environnement des deux VM

Ce document complète les étapes 3 à 6. Il décrit les informations fournies
et les vérifications à prévoir. Aucune connexion distante, installation,
modification réseau ou création de conteneur n'a été effectuée par l'assistant.

## Informations observées

Source : sorties `ip a` transmises par l'utilisateur.

| Élément | toolsG2 | labG2 |
|---|---|---|
| Compte indiqué dans l'invite | NetOps | NetOps |
| Interface principale | ens18, UP | ens18, UP |
| Adresse IPv4 | 10.108.2.29/24, dynamic | 10.108.2.65/24, dynamic |
| Sous-réseau d'infrastructure | 10.108.2.0/24 | 10.108.2.0/24 |
| MTU d'ens18 | 1500 | 1500 |
| docker0 | 172.17.0.1/16, sans carrier | 172.17.0.1/16, sans carrier |
| Autre bridge | br-4b600d8327cc, 172.18.0.1/16, DOWN | br-c5b16cfe8a39, 172.18.0.1/16, UP |
| Interfaces veth montrées | Aucune dans la sortie fournie | Deux sur le bridge 172.18.0.1/16 |

La présence d'interfaces Docker ne démontre pas que le moteur est actuellement
joignable, que Containerlab est installé ou qu'une image cEOS est disponible.
Un bridge sans carrier ne suffit pas à conclure à une panne Docker.
Le nombre de conteneurs existants doit être obtenu auprès de Docker, sans
le déduire du seul nombre d'interfaces veth.

Les deux VM appartiennent au même sous-réseau IPv4. Leur joignabilité mutuelle,
leurs accès SSH et les autorisations du compte restent à vérifier.
La passerelle par défaut et le DNS ne figurent pas dans ces sorties.

## Répartition proposée

| VM | Rôle prévu | Ressources à vérifier |
|---|---|---|
| toolsG2, 10.108.2.29 | Dépôt de travail, Ansible/Jinja2, gnmic, Prometheus et Grafana | CPU, mémoire, disque, outils déjà installés et ports disponibles |
| labG2, 10.108.2.65 | Docker/Containerlab, P1/P2, trois PE, quatre CE, quatre hosts | Capacité pour 9 cEOS et 4 hosts, images présentes, charge existante |

Les 13 conteneurs du PoC sont prévus sur labG2. Si les trois services
d'observabilité sont chacun conteneurisés sur toolsG2, le projet représente
16 conteneurs répartis sur les deux VM, hors conteneurs préexistants.
Les deux VM ne sont pas incluses dans ce total de conteneurs.

## Adressage et accès de management

| Usage | Réseau | Statut |
|---|---|---|
| Accès aux VM | 10.108.2.0/24 | Observé |
| Réseaux Docker existants | 172.17.0.0/16 et 172.18.0.0/16 | Observés sur les deux VM |
| Management des équipements sur labG2 | 172.31.255.0/24, passerelle de bridge 172.31.255.1 | Proposition |
| LAN des filiales | 10.10.10.0/24, 10.10.20.0/24, 10.20.10.0/24, 10.20.20.0/24 | Proposition |
| Loopbacks | Adresses /32 dans 10.255.0.0/24 | Proposition |
| Liens CE-PE | Quatre /30 dans 172.16.0.0/28 | Proposition |
| Liens PE-P et P-P | Sept /30 dans 10.0.0.0/27 | Proposition |

Le plan proposé ne chevauche pas les sous-réseaux observés. Vérifier aussi
les autres routes, les VPN éventuels et les réseaux Docker non montrés.
Les bridges 172.18.0.0/16 des deux VM sont locaux à chaque hôte.
Ne pas utiliser leur adresse identique comme preuve d'une liaison entre VM.

Chemin de gestion à préparer : toolsG2, puis labG2 en 10.108.2.65,
puis chaque équipement en 172.31.255.x. Pour un accès routé, il faudra
vérifier une route adaptée depuis toolsG2, le transfert IP sur labG2,
les autorisations de filtrage et le chemin retour. La configuration par
défaut d'un bridge Docker ne garantit pas l'accès depuis une autre VM.
Une route seule ne prouve donc pas que l'accès fonctionnera.

Cette conception est à valider selon le laboratoire fourni. Aucune route,
règle de pare-feu, publication de port ou modification Docker n'est appliquée.
Le contrôle de la connectivité précédera tout provisionnement futur.

Les IP individuelles des neuf cEOS doivent rester dans l'inventaire eAPI.
L'adresse 10.108.2.65 désigne la VM et ne permet pas d'identifier à elle seule
chacun de ses routeurs. Les LAN clients ne doivent pas être annoncés sur le
réseau d'infrastructure pour rendre le management accessible.

## Flux à documenter avant la réalisation

| Origine | Destination | Usage futur | Port prévu |
|---|---|---|---|
| Poste d'administration | toolsG2 / labG2 | Administration des VM | SSH, généralement TCP/22, à confirmer |
| toolsG2 | Chaque cEOS de labG2 | Ansible via eAPI | HTTPS TCP/443 |
| gnmic sur toolsG2 | Chaque cEOS de labG2 | Collecte gNMI | TCP/6030 prévu, à confirmer sur l'image |
| Prometheus sur toolsG2 | gnmic | Lecture des métriques | À définir dans la future configuration |
| Grafana sur toolsG2 | Prometheus | Requêtes de métriques | À définir dans la future configuration |

L'authentification et la validation des certificats eAPI restent à préparer.
Le compte Linux `NetOps` ne définit pas le compte de connexion aux cEOS.
Si gnmic s'exécute dans un conteneur, son propre chemin réseau et le retour
doivent être vérifiés en plus de ceux de la VM toolsG2.

## Vérifications en lecture seule à prévoir

Ces commandes sont des points de contrôle documentés. Elles n'ont pas été
exécutées sur les VM par l'assistant. Les échecs éventuels peuvent dépendre
des droits du compte et doivent être relevés sans modifier ces droits ici.

Sur chacune des deux VM :

```sh
hostname
ip -br address
ip route
nproc
free -h
df -h
docker version
docker info
docker ps -a
docker network ls
ss -lnt
```

Depuis toolsG2, pour examiner le chemin vers labG2 :

```sh
ip route get 10.108.2.65
ping -c 3 10.108.2.65
command -v ansible-playbook
command -v git
command -v gnmic
```

Depuis labG2, pour examiner le chemin vers toolsG2 et les outils du labo :

```sh
ip route get 10.108.2.29
ping -c 3 10.108.2.29
command -v containerlab
docker image ls
```

Un refus ICMP ne suffit pas à conclure que SSH ou les autres services sont
inaccessibles. Après identification de l'exécutable Containerlab, relever sa
version. Après identification des réseaux Docker, inspecter leurs sous-réseaux
et leurs membres. Aucun conteneur existant ne doit être supprimé ou relancé
pour réaliser ces contrôles.

## Points encore ouverts

- Confirmer les rôles proposés des deux VM et leurs capacités.
- Vérifier le moteur Docker, Containerlab et les images cEOS sur labG2.
- Identifier les conteneurs déjà présents sur les deux VM.
- Préciser l'accès de toolsG2 aux futurs équipements de labG2.
- Prévoir une réservation DHCP ou une autre méthode validée pour stabiliser
  les IP des VM, ou mettre à jour les variables après changement de bail.
- Confirmer le routage, le filtrage, l'authentification et les certificats.

Références techniques : [réseaux bridge Docker](https://docs.docker.com/engine/network/drivers/bridge/)
et [filtrage réseau Docker](https://docs.docker.com/engine/network/packet-filtering-firewalls/).
