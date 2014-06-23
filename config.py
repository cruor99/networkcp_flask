__author__ = 'cruor'
import os


CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'


basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(basedir, 'tmp')
ALLOWED_EXTENSIONS = set(['zip'])


#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_DATABASE_URI = 'mysql://steve:12Karen34@84.49.16.101/servercp'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# email server
#MAIL_SERVER = 'mail.broadpark.no'
#MAIL_PORT = 25
#MAIL_USE_TLS = False
#MAIL_USE_SSL = False
#MAIL_USERNAME = 'you'
#MAIL_PASSWORD = 'your-password'

MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'kliknes@gmail.com'
MAIL_PASSWORD = 'unh4ck4bl3'


# administrator list
ADMINS = ['post@gameserver.no']