import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from config import basedir, ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD
from flask.ext.mail import Mail

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
oid = OpenID(app, os.path.join(basedir, 'tmp'))
mail = Mail(app)

from app import views, models


