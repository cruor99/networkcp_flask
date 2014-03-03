__author__ = 'cruor'
from app import db
from werkzeug import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import *
ROLE_USER = 0
ROLE_ADMIN = 1
ROLE_PREMIUM = 2

class User(db.Model):
    cust_id = db.Column(db.Integer, primary_key = True)
    cust_username = db.Column(db.String(64), unique = True)
    cust_mail = db.Column(db.String(120), unique = True)
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    pwdhash = db.Column(db.String(120))
    created = db.Column(db.DATETIME)
    cust_fname = db.Column(db.String(30))
    cust_lname = db.Column(db.String(30))
    cust_phone = db.Column(db.String(12))
    cust_notes = db.Column(db.TEXT)

    def __init__(self, username, password, email, fname, lname, phone):
        self.cust_username = username
        self.pwdhash = generate_password_hash(password)
        self.cust_mail = email
        self.role = ROLE_USER
        self.created = datetime.utcnow()
        self.cust_fname = fname
        self.cust_lname = lname
        self.cust_phone = phone

    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.nickname)

class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    cust_id = db.Column(db.Integer, ForeignKey('user.cust_id'), primary_key=True)

class Server(db.Model):
    server_id = db.Column(db.Integer, primary_key=True)
    server_name = db.Column(db.String(30))
    server_ip = db.Column(db.String(30))


class Port(db.Model):
    port_id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, ForeignKey('server.server_id'))
    port_no = db.Column(db.Integer)
    port_used = db.Column(db.Boolean)

class Subscription(db.Model):
    sub_id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, ForeignKey('server.server_id'))
    sub_name = db.Column(db.String(100))
    sub_description = db.Column(db.Text)
    sub_type = db.Column(db.String(50))
    sub_days = db.Column(db.Integer)
    sub_hours = db.Column(db.Integer)
    sub_mnd = db.Column(db.Integer)
    sub_limit = db.Column(db.Integer)
    sub_pris = db.Column(db.Float)
    sub_active = db.Column(db.Boolean)
    sub_sms_payment = db.Column(db.Boolean)

class Orderline(db.Model):
    orderl_id = db.Column(db.Integer, primary_key=True)
    port_id = db.Column(db.Integer, ForeignKey('port.port_id'))
    sub_id = db.Column(db.Integer, ForeignKey('subscription.sub_id'))
    order_id = db.Column(db.Integer, ForeignKey('order.order_id'))
    orderl_create = db.Column(db.Date)
    orderl_expire = db.Column(db.Date)