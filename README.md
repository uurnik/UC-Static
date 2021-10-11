# Setup Instructions

### Install docker
> `sudo curl -fsSL https://get.docker.com -o get-docker.sh`

if curl is not install, you can install using 
> `sudo apt install curl`

Install docker-compose
> `sudo apt install docker-compose`

### Clone the repo
> `git clone https://github.com/uurnik/uurnikconnect.git`


## Environment 

Create `.env` file in the root of the project by refering to the `env.example` file

Build & Start
(Dev)
> docker-compose up

(Production)
> docker-compose up -f docker-compose-prod.yaml


### Dev
Following ports needs to exposed:

- 53/tcp        (dns)
- 53/udp        (dns)
- 8001/tcp      (uurnik connect api)
- 8080/tcp      (dnsupdater api)


> **_NOTE_** In development environment `DEBUG` should be set to `True` which will turn on Django debuging along Scrapli & Nornir logs

[Poetry](https://python-poetry.org/) is used to create/manage python virtual environment

### Production
In production environment, nginx is used to proxy the reqeust to desired application

- /nic -> 8080
- /api -> 8000

Following ports needs to exposed in production:
- 53/tcp
- 53/udp
- 80,443


## Tools Used for Network Automation

- [Scrapli](https://github.com/carlmontanari/scrapli)
- [Netmiko](https://github.com/ktbyers/netmiko)
- [Nornir](https://nornir.readthedocs.io/en/v2.5.0/)
- [TTP](https://ttp.readthedocs.io/en/latest/)


## Frontend
Frontend of the uurnikconnect is build with Vuejs and Vuetify.
For building topology diagram [viz js](https://visjs.github.io/vis-network/docs/network/) is used.
