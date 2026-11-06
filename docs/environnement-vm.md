# Environnement technique — relevé du 6 novembre 2026

Les informations ci-dessous associent l'état communiqué par l'utilisateur et
les contrôles SSH effectués pendant cette journée. Les résultats réseau sont
dans [le journal du jour](journal-2026-11-06.md).

## Rôles retenus

| VM | Adresse ens18 | Rôle de cette phase |
|---|---|---|
| labG2 / LAB | 10.108.2.65/24 | Docker, Containerlab, 9 cEOS, 4 hosts, configuration et tests ; premier contrôleur Ansible |
| toolsG2 / TOOLS | 10.108.2.29/24 | Copie Git du projet, documentation, environnement Nautobot existant, futurs outils complémentaires |

Les adresses sont attribuées par DHCP. Une réservation reste souhaitable.
Le compte NetOps possède les droits Docker et sudo sans mot de passe.
Les connexions SSH depuis le poste d'administration ont fonctionné après
connexion VPN et authentification. Aucun identifiant n'est enregistré dans Git.

## Ressources et logiciels

| Élément | LAB | TOOLS |
|---|---|---|
| RAM totale | 23 Gio | 11 Gio |
| RAM disponible avant déploiement | 22 Gio | 11 Gio |
| CPU | 8 cœurs, confirmé | 4 cœurs, confirmé |
| Espace libre sur / après déploiement | 66 Go | 66 Go |
| Docker client et serveur | 29.7.2, confirmé | 29.7.2, confirmé |
| Containerlab | 0.79.0 au déploiement, **0.82.0 actuellement** | Exécutable absent du PATH |
| Ansible | ansible-core 2.21.3, confirmé dans pipx | Exécutable absent du PATH |
| Python | 3.12.3, confirmé | 3.12.3, confirmé |
| Git | Exécutable disponible | 2.43.0, confirmé en SSH |

Dans le Python système de LAB, les imports renvoient **PyYAML 6.0.1 et
Jinja2 3.1.2**. Dans l'environnement pipx d'Ansible, les versions sont bien
**PyYAML 6.0.3 et Jinja2 3.1.6**, conformément au relevé fourni. Ansible est
accessible à `/home/NetOps/.local/bin/ansible` ; une commande SSH non interactive
peut ne pas inclure ce répertoire dans son PATH.

Après déploiement, LAB conserve environ **11 Gio de RAM disponible**. Le relevé
de 22 Gio correspondait à l'état avant le démarrage des 13 conteneurs.
Une mise à jour vers **Containerlab 0.82.0** a été observée dans le terminal
de VS Code pendant la configuration de l'extension. Le déploiement initial
et sa première campagne de tests ont bien utilisé 0.79.0.

## Docker avant déploiement

Sur LAB, images confirmées : `ceos:4.36.1F`, network-multitool:latest,
ghostwire:latest, packetflix:latest et wireshark-vnc-docker:latest
(les quatre dernières sous les namespaces communiqués). Le PoC utilise
les deux premières sans téléchargement. Le tag latest du host est mutable :
conserver son ID/digest avec les preuves avant un futur changement d'image.

EdgeShark et Ghostwire sont actifs depuis trois jours au moment du contrôle.
Ils sont conservés. Leurs réseaux Docker sont `172.17.0.0/16` et
`172.18.0.0/16`, sans chevauchement avec `172.31.255.0/24` proposé pour le PoC.

Sur TOOLS, le contexte Docker `default` contient cinq conteneurs Nautobot,
PostgreSQL, Redis, Celery Worker et Celery Beat. **Tous sont arrêtés** au
moment du contrôle SSH. Les mentions antérieures « conteneurs présents »
ne signifiaient donc pas « services en fonctionnement ». Ils n'ont été
ni démarrés, ni supprimés, ni reconfigurés pendant ce travail.

## Accès et séparation des réseaux

L'utilisateur a validé la connectivité LAB vers TOOLS et TOOLS vers LAB.
La route par défaut de LAB passe par `10.108.2.254` sur ens18.
Le management des 13 conteneurs utilise un bridge local à LAB :
`netops-mgmt`, `172.31.255.0/24`, passerelle `172.31.255.1`.

Les routeurs placent Management0 dans une VRF MGMT dédiée. Les interfaces
de données et les loopbacks restent hors de cette VRF. Cela évite de valider
par erreur le backbone avec un détour par le réseau de management.
Aucun compte EOS distant ni eAPI/gNMI n'est provisionné dans cette phase.
L'administration se fait avec `docker exec` depuis LAB.

L'accès routé depuis TOOLS aux conteneurs nécessite encore un travail sur
les routes, le filtrage Docker, l'authentification et les certificats.
Ansible reste donc sur LAB pour commencer. Les adresses et paramètres eAPI
de l'inventaire constituent une préparation pour la phase d'automatisation.
