__author__ = 'cruor'
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, PasswordField, SelectField, RadioField
from wtforms import validators
from wtforms_alchemy import ModelForm
from models import User
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from sqlalchemy.orm import load_only
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import Table, MetaData
from server import Server



def listallu():
    return User.query

class PropertiesForm(Form):
    serv = Server()
    props = TextField('props')
    value = TextField('values')

class UadminForm(Form):
    role = SelectField('role', choices=[(1, 'standard'), (2, 'Admin'), (3, 'Premium')])
    usersel = QuerySelectField('usersel', query_factory=listallu, allow_blank=True, get_label=str)

class PasswordForm(Form):
    usersel = QuerySelectField('usersel', query_factory=listallu, allow_blank=True, get_label=str)
    pwdfield = PasswordField('Password')

class SubscriptionForm(Form):
    subsel = RadioField('Subscriptions', choices=[(1, '1-month'), (2, '3-month'), (3, '6-month'), (4, '12-month')])

class LoginForm(Form):
    #openid = TextField('openid', validators = [validators.Required()])
    remember_me = BooleanField('remember_me', default = False)
    password = PasswordField('Password', validators=[validators.Required()])
    email = TextField('eMail', validators=[validators.Required()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(LoginForm, self).__init__(*args, **kwargs)

class signup_form(Form):
    username = TextField('Username', validators=[validators.Required()])
    password = PasswordField('Password', validators=[validators.Required()])
    confirm = PasswordField('Confirm Password', validators=[validators.Required(), validators.EqualTo('confirm', message='Passwords must match')])
    email = TextField('eMail', validators=[validators.Required()])
    fname = TextField('First Name', validators=[validators.Required()])
    lname = TextField('Last Name', validators=[validators.Required()])
    phone = TextField('Phone Number', validators=[validators.Required()])
    accept_tos = BooleanField('I accept the TOS', default = False, validators=[validators.Required()])

    #catches csrf_enabled for site security, and to prevent it from being sent for validation
    #this would force forms.validate() in views.py def signup() to always return False
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(signup_form, self).__init__(*args, **kwargs)