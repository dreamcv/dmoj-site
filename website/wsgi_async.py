import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

import pymysql
pymysql.install_as_MySQLdb()

import gevent.monkey
gevent.monkey.patch_all()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
