import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

try:
    import MySQLdb
except ImportError:
    import pymysql
    pymysql.install_as_MySQLdb()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
