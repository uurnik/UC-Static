# Defaults

Field | Value | Description
------|--------|-----------
Tunnel Interface | 414 | Tunnel interface number
LoopBack Interface | 0 | -
ASN | 65414 | ASN for BGP configuration
Policy Number | 22 | Policy Number for IPsec configuration
IPsec Key | uurnik123 | IPsec key for IPsec configuration
Transform Set | UURNIK | Transform set for IPsec configuration
Profile name | UURNIK_CONNECT | Profile name for IPsec configuration
Tunnel Pool | 172.27.0.0/16 | IP pool from which IPs are assigned to the tunnel interface of the hosts
Access list | uurnik | access-list name to be used for NAT
Front VRF | INTERNET | -
Inside VRF | LAN | -
Kron Policy-list | uurnik | Name for the kron policy which is used to schedule to run the TCL script
NHRP authentication | 1234 | -
NHRP network-id | 1 | -
Peer-Group | UURNIK_CONNECT | -
Peer-Group Password | {IPsec Key} | -
IP SLA | 214 | IP SLA process number
Track object (SLA) | {IP SLA} | track object number
VRRP group | {IP SLA} | VRRP group number


## Scrapli TimeOuts

Field | Value 
------|--------
timeout-ops | 45s
timeout-transport | 45s
timeout-socket | 45s