# Dependencies & Housekeeping

## Project Management

Poetry is used for managing the UC API package.
Poetry provides a custom installer that will install poetry isolated from the rest of your system by vendorizing its dependencies


## Dependency file for UC API
 **pyproject.toml**:

    [tool.poetry]
    name = "uurnik_connect_api"
    version = "1.0"
    description = ""
    authors = ["Uurnik Systems <talha.javaid@uurnik.com>"]

    [tool.poetry.dependencies]
    python = "^3.8"
    nornir = "2.5"
    ttp = "^0.6.0"
    djangorestframework = "3.11.0"
    django-cors-headers = "^3.6.0"
    django-rest-knox = "^4.1.0"
    dnspython = "^2.0.0"
    pysnmp = "^4.4.12"
    beautifulsoup4 = "^4.9.3"
    requests-ntlm2 = "^6.2.8"
    mysqlclient = "^2.0.3"
    requests = "^2.25.1"
    nornir-scrapli = "2020.7.12"
    scrapli = {extras = ["textfsm"], version = "^2020.12.31"}
    scrapli-ssh2 = "^2020.10.24"


    [tool.poetry.dev-dependencies]
    pylint = "^2.6.0"
    sphinx = "^3.2.1"
    sphinx-rtd-theme = "^0.5.0"
    recommonmark = "^0.6.0"
    sphinx_markdown_tables = "^0.0.15"
    rst2pdf = "^0.97"

    [build-system]
    requires = ["poetry>=0.12"]
    build-backend = "poetry.masonry.api"


## Licences for UC dependencies

Package Name | License
-------------|---------
Nornir | Apache License 2.0
Netmiko | MIT License
Napalm | Apache License 2.0
Django REST framework |  <https://github.com/encode/django-rest-framework/blob/master/LICENSE.md>
django-rest-knox | MIT License
django-cors-headers | MIT License
pyarmor |  <https://github.com/dashingsoft/pyarmor/blob/master/LICENSE>
gunicorn | <https://github.com/benoitc/gunicorn/blob/master/LICENSE>
ttp | MIT License
dnspython | <https://github.com/rthalley/dnspython/blob/master/LICENSE>
scrapli | MIT License 