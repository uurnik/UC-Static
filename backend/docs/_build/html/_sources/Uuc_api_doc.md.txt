# Uurnik Connect API

## Configuration & Hosts

 API Endpoint | Method | Use
----------|--------|-----
api/hosts/| GET,POST | To Get & upload Host information to DB
api/hosts/| DELETE | To delete host from inventory
api/configure/< int:option >/ | POST | To deploy DMVPN on all hosts in the DB
api/branch/< str:ip >/| POST,DELETE | To Add or Delete a spoke from the Network
api/hub/< str:ip >/| POST,DELETE | To Add or Delete a Hub from the network 
api/tear-down/| DELETE | To remove configuration from all the hosts in network
api/neighbors/| GET | To get CDP information from all the Hosts in the DB
api/ip-sla/ | POST | To configure VRRP with IP SLA tracking
api/interfaces/< str:ip > | GET | Get interfaces info
api/device-hardening | POST | Push device hardening commands
api/facts/ | GET | Gather device facts
api/copp/ | POST | Configure control plane policing



## Users

API Endpoint | Method | Use
----------|--------|-----
api/users/register/ | POST | Registers new user (only super user have permission)
api/users/login/ | POST | User Login 
api/users/logout/ | POST | User Logout
api/users/password_reset/ | PUT | To change user password
api/users/delete/< str:username >/ | DELETE | To delete user (only super user have permission)


## Misc

API Endpoint | Method | Use
----------|--------|-------
api/ping/| GET | To check reachability of all the Hosts in the DB
api/alive/ | GET | To check the ssh connectivity
api/access-type | GET | Get deployed access type