# Overview


## Architecture Overview

![Architecture](./_static/Uuc_API_arch.png)

## Features
- Deploy DMVPN over IPsec with BGP routing
- User can select access type how to configure the network ( Private WAN only, Private WAN + DIA, Private WAN + DIA + other services )
- Spokes can be added or removed individually in  already deployed network
- Hubs(other than primary) can be added or removed individually in already deployed network
- User can check for Hosts reachability
- User can fetch CDP information


## Prerequisites
- User must give WAN IP of the Hosts
- There Must be a default route on the Device
- Given ssh user for the host must of priviledge 15 

## Supported Devices
- Cisco IOS
- Cisco IOS-XE



