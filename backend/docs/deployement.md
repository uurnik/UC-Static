# Deploy Uurnik Connect in Test Environment

- Install poetry
```
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -
```

- append poetry executable path in PATH env variable
```
PATH=$PATH:~/.poetry/bin/
```

- check if poetry is working correctly
```
poetry --version
```

- configure poetry to create virtual environment within the project directory
```
poetry config virtualenvs.in-project true
poetry config
```

- install & configure git
```
sudo apt install git
git config --global user.name "username"
git config --global user.email "email"
```

- clone UUC_API repo from dev branch
```
git clone --branch dev https://github.com/uurnik/Uurnik_connect_API-.git
```

- install dependencies for python mysqlclient
```
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
```

- cd into project and install dependencies
```
poetry install
```

- install and start mariadb
```
sudo apt install mariadb-server
systemctl enable --now mariadb
mysql_secure_installation
```

- access mariadb shell ,create user & database
```
sudo mysql -u root -p
```


```
CREATE DATABASE UURNIK;
CREATE USER 'uurnik'@localhost IDENTIFIED BY 'admin';
GRANT ALL PRIVILEGES ON *.* TO 'uurnik'@localhost IDENTIFIED BY 'admin';
FLUSH PRIVILEGES;
exit;
```

- disable firewall
```
sudo ufw allow port 8000
```

- cd into Uuc_api/api
```
python3 manage.py createsuperuser
python3 manage.py migrate
python3 manage.py runserver 0.0.0.0:800     # will start development server on port 8000
```


## Tasks before Deployement

- Command for saving config must be included in template (or after deployment validation)
- Check License information
- Check model and get device's max throughput from model_spec file ( for COPP)
- Remove print statements ( print statements are for debugging purposes only)
- DDNS server must be configured
- Authentication decorators are commented and must be uncommented to use API token authentication
