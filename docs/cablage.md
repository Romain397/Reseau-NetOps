# Câblage et adressage

Généré depuis `data/fabric.yml`. `ethN` dans Containerlab correspond à
`EthernetN` dans EOS. Le management utilise `eth0` / `Management0`.

| Lien | Extrémité A | IPv4 A | Extrémité B | IPv4 B | Usage |
|---:|---|---|---|---|---|
| 1 | pe-par:Ethernet3 | 172.16.0.1/30 | ce-a-par:Ethernet1 | 172.16.0.2/30 | access |
| 2 | ce-a-par:Ethernet2 | 10.10.10.1/24 | host-a-par:eth1 | 10.10.10.10/24 | lan |
| 3 | pe-avi:Ethernet3 | 172.16.0.5/30 | ce-a-avi:Ethernet1 | 172.16.0.6/30 | access |
| 4 | ce-a-avi:Ethernet2 | 10.10.20.1/24 | host-a-avi:eth1 | 10.10.20.10/24 | lan |
| 5 | pe-par:Ethernet4 | 172.16.0.9/30 | ce-b-par:Ethernet1 | 172.16.0.10/30 | access |
| 6 | ce-b-par:Ethernet2 | 10.20.10.1/24 | host-b-par:eth1 | 10.20.10.10/24 | lan |
| 7 | pe-bdx:Ethernet3 | 172.16.0.13/30 | ce-b-bdx:Ethernet1 | 172.16.0.14/30 | access |
| 8 | ce-b-bdx:Ethernet2 | 10.20.20.1/24 | host-b-bdx:eth1 | 10.20.20.10/24 | lan |
| 9 | pe-par:Ethernet1 | 10.0.0.1/30 | p1:Ethernet1 | 10.0.0.2/30 | backbone |
| 10 | pe-par:Ethernet2 | 10.0.0.5/30 | p2:Ethernet1 | 10.0.0.6/30 | backbone |
| 11 | pe-avi:Ethernet1 | 10.0.0.9/30 | p1:Ethernet2 | 10.0.0.10/30 | backbone |
| 12 | pe-avi:Ethernet2 | 10.0.0.13/30 | p2:Ethernet2 | 10.0.0.14/30 | backbone |
| 13 | pe-bdx:Ethernet1 | 10.0.0.17/30 | p1:Ethernet3 | 10.0.0.18/30 | backbone |
| 14 | pe-bdx:Ethernet2 | 10.0.0.21/30 | p2:Ethernet3 | 10.0.0.22/30 | backbone |
| 15 | p1:Ethernet4 | 10.0.0.25/30 | p2:Ethernet4 | 10.0.0.26/30 | backbone |
