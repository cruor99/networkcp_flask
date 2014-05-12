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
        return '%s' % (self.cust_username)


class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    cust_id = db.Column(db.Integer, ForeignKey('user.cust_id'), primary_key=True)
    orderident = db.Column(db.String(30))
    def __init__(self, cust_id, orderident):
        self.cust_id = cust_id
        self.orderident = orderident

class Serverreserve(db.Model):
    server_id = db.Column(db.Integer, primary_key=True)
    server_name = db.Column(db.String(30), unique=True)
    server_ip = db.Column(db.String(30), unique=True)

    def __init__(self, server_name, server_ip):
        self.server_name = server_name
        self.server_ip = server_ip

    def __repr__(self):
        return '%i, %s, %s' % (self.server_id, self.server_name, self.server_ip)


class Port(db.Model):
    port_id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, ForeignKey('serverreserve.server_id'))
    port_no = db.Column(db.Integer)
    port_used = db.Column(db.Integer)

    def __init__(self, server_id, port_no, port_used):
        self.server_id = server_id
        self.port_no = port_no
        self.port_used = port_used

    def __repr__(self):
        return '[%i, %i]' % (self.port_no, self.server_id)



class Subscription(db.Model):
    sub_id = db.Column(db.Integer, primary_key=True)
    sub_name = db.Column(db.String(100))
    sub_description = db.Column(db.Text)
    sub_type = db.Column(db.String(50))
    sub_days = db.Column(db.Integer)
    sub_hours = db.Column(db.Integer)
    sub_mnd = db.Column(db.Integer)
    sub_limit = db.Column(db.Integer)
    sub_pris = db.Column(db.Float)

    def __init__(self, sub_name, sub_description, sub_type, sub_days, sub_hours, sub_mnd,\
                 sub_limit, sub_pris):
        self.sub_name = sub_name
        self.sub_description = sub_description
        self.sub_type = sub_type
        self.sub_days = sub_days
        self.sub_hours = sub_hours
        self.sub_mnd = sub_mnd
        self.sub_limit = sub_limit
        self.sub_pris = sub_pris

    def __repr__(self):
        return '%s' % (self.sub_id)

class Orderline(db.Model):
    orderl_id = db.Column(db.Integer, primary_key=True)
    port_id = db.Column(db.Integer, ForeignKey('port.port_id'))
    sub_id = db.Column(db.Integer, ForeignKey('subscription.sub_id'))
    order_id = db.Column(db.Integer, ForeignKey('order.order_id'))
    orderl_create = db.Column(db.Date)
    orderl_expire = db.Column(db.Date)
    order_payed = db.Column(db.String(30))

    def __init__(self, port_id, sub_id, order_id, orderl_create, orderl_expire, order_payed):
        self.port_id = port_id
        self.sub_id = sub_id
        self.order_id = order_id
        self.orderl_create = orderl_create
        self.orderl_expire = orderl_expire
        self.order_payed = order_payed

    def __repr__(self):
        return 'Order ID: %s, Expiration date: %s' % (self.orderl_id, self.orderl_expire)

class Giftcard(db.Model):
    giftcard_id = db.Column(db.Integer, primary_key=True)
    sub_id = db.Column(db.Integer, ForeignKey('subscription.sub_id'))
    gift_code = db.Column(db.String(100), unique=True)
    expiration = db.Column(db.Date)
    in_use = db.Column(db.Boolean)

    def __init__(self, sub_id, gift_code, expiration):
        self.sub_id = sub_id
        self.gift_code = gift_code
        self.expiration = expiration

    def __repr__(self):
        return "ID: %s Subscription ID: %s Gift Code: %s \n Expiration Date: %s" % (self.giftcard_id, self.sub_id, self.gift_code, self.expiration)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    body = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime)
    type = db.Column(db.String(10))
    cust_id = db.Column(db.Integer, ForeignKey('user.cust_id'))

    def __repr__(self):
        return 'Title: %s  ' \
               '\n' \
               'Body: %s' % (self.title, self.body)

class VtOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slots = db.Column(db.Integer)
    price = db.Column(db.Integer)
    expiration = db.Column(db.Date)
    port_id = db.Column(db.Integer, ForeignKey('port.port_id'))
    cust_id = db.Column(db.Integer, ForeignKey('user.cust_id'))

    def __init__(self, slots, price, expiration, port_id, cust_id):
        self.slots = slots
        self.price = price
        self.expiration = expiration
        self.port_id = port_id
        self.cust_id = cust_id