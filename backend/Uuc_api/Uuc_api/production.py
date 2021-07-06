from .settings import *
import os


DEBUG = os.environ['DEBUG'] == 'True'
if DEBUG:
    DEBUG = True
else:
    DEBUG = False

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = [os.environ["ALLOWED_HOSTS"]]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["MY_SQL_DATABASE"],
        "USER": os.environ["MYSQL_USER"],
        "PASSWORD": os.environ["MYSQL_USER_PASS"],
        "HOST": "db",
        "PORT": 3306,
        "OPTIONS": {"init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
    }
}
