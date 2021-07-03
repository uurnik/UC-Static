"""
WSGI config for Uuc_api project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""
"""
WSGI config for Uuc_api project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Uuc_api.production')
DJANGO_SETTINGS_MODULE = os.environ["DJANGO_SETTINGS_MODULE"]

application = get_wsgi_application()
