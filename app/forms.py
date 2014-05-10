__author__ = 'cruor'
from flask.ext.wtf import Form
from wtforms.fields.html5 import DecimalRangeField
from wtforms import TextField, BooleanField, PasswordField, SelectField, RadioField, DateField
from wtforms import validators
from wtforms_alchemy import ModelForm
from models import *
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from server import Server


def listallu():
    return User.query


def listserv():
    return Serverreserve.query


def listport():
    return Port.query


def listsub():
    return Subscription.query


class VentOrder(Form):
    slots = DecimalRangeField('Slots', '100', '10')
    months = DecimalRangeField('Months')

class GiftCardCheckin(Form):
    giftcode = TextField('Skriv inn Gavekort koden:')


class GiftCardForm(Form):
    sub_id = QuerySelectField('Select Subscription: ', query_factory=listsub)
    gift_code = TextField('Create Gift Code')
    expiration = DateField('Create Expiration date: (YYYY-MM-DD)', format='%Y-%m-%d')

class ServerForm(Form):
    servername = TextField('Server Name', validators=[validators.Required()])
    serverip = TextField('Server IP', validators=[validators.Required()])


class PortForm(Form):
    server = QuerySelectMultipleField('Select Server (Hold CTRL to select several servers)', query_factory=listserv)
    portno = TextField('Port Number')
    portused = SelectField('Is the Port in Use', choices=[(1, "Yes"), (2, "No")])


class UpdatePortForm(Form):
    server = QuerySelectField('Select Server', query_factory=listserv)
    portno = TextField('Port Number')
    portused = SelectField('Is the Port in Use', choices=[(1, "Yes"), (2, "No")])


class DeleteserverForm(Form):
    serversel = QuerySelectField('Select Server', query_factory=listserv)


class DeleteportForm(Form):
    portsel = QuerySelectField('Select Port', query_factory=listport)


class SubManageForm(Form):
    server_id = TextField('Server ID', validators=[validators.Required()])
    sub_name = TextField('Subscription Name', validators=[validators.Required()])
    sub_description = TextField('Subscription Description', validators=[validators.Required()])
    sub_type = TextField('Subscription Type', validators=[validators.Required()])
    sub_days = TextField('Subscription Days')
    sub_hours = TextField('Subscription Hours')
    sub_mnd = TextField('Subscription Months')
    sub_limit = TextField('Subscription Limit', validators=[validators.Required()])
    sub_pris = TextField('Subscription Price', validators=[validators.Required()])
    sub_active = BooleanField('Subscription Active')
    sub_sms_payment = BooleanField('SMS Payment')


class PropertiesForm(Form):
    serv = Server()
    props = TextField('Property')
    value = TextField('Value')


class CommandForm(Form):
    command = TextField('Command')


class UadminForm(Form):
    role = SelectField('Select Role', choices=[(0, 'Standard'), (1, 'Admin'), (2, 'Premium')])
    usersel = QuerySelectField('Select User', query_factory=listallu, allow_blank=True, get_label=str)


class DeleteuserForm(Form):
    usersel = QuerySelectField('Select User', query_factory=listallu, allow_blank=True, get_label=str)


class UserinfoForm(Form):
    oldpwd = PasswordField('Current Password', validators=[validators.Required()])
    pwdfield = PasswordField('Password')
    confirm = PasswordField('Confirm Password')
    email = TextField('eMail')
    fname = TextField('First Name')
    lname = TextField('Last Name')
    phone = TextField('Phone Number')


class AdmininfoForm(Form):
    usersel = QuerySelectField('Select User', query_factory=listallu, allow_blank=True, get_label=str)
    username = TextField('Username')
    pwdfield = PasswordField('Password')
    email = TextField('eMail')
    fname = TextField('First Name')
    lname = TextField('Last Name')
    phone = TextField('Phone Number')
    note = TextField('Note')


class SubscriptionForm(Form):
    subsel = RadioField('<h3>Select Subscription:</h3>')


class LoginForm(Form):
    remember_me = BooleanField('remember_me', default = False)
    password = PasswordField('Password', validators=[validators.Required()])
    email = TextField('Username or eMail', validators=[validators.Required()])
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(LoginForm, self).__init__(*args, **kwargs)


class VtEditForm(Form):
    key = SelectField('.Ini Key', choices=[('name', 'name'), ('phonetic', 'phonetic'), ('auth', 'auth'), ('duplicates', 'duplicates'), ('adminpassword', 'adminpassword'), ('password', 'password'), ('sendbuffer', 'sendbuffer'), ('recvbuffer', 'recvbuffer'), ('diag', 'diag'), ('logontimeout', 'logontimeout'), ('closestd', 'closestd'), ('timestamp', 'timestamp'), ('pingrate', 'pingrate'), ('extrabuffer', 'extrabuffer'), ('chanwidth', 'chanwidth'), ('chandepth', 'chandepth'), ('chanclients', 'chanclients'), ('disablequit', 'diasablequit'), ('voicecodec', 'voicecodec'), ('voiceformat', 'voiceformat'), ('silentlobby', 'silentlobby'), ('autokick', 'autokick'), ('codexmaxbw', 'codexmaxbw')])
    value = TextField('New Value')


class signup_form(Form):
    username = TextField('Username*', validators=[validators.Required()])
    password = PasswordField('Password*', validators=[validators.Required()])
    confirm = PasswordField('Confirm Password*', validators=[validators.Required(), validators.EqualTo('password', message='Passwords must match')])
    email = TextField('eMail*', validators=[validators.Required()])
    fname = TextField('First Name*', validators=[validators.Required()])
    lname = TextField('Last Name*', validators=[validators.Required()])
    phone = TextField('Phone Number (numbers only)')
    accept_tos = BooleanField('I accept the TOS*', default = False, validators=[validators.Required()])
    #catches csrf_enabled for site security, and to prevent it from being sent for validation
    #this would force forms.validate() in views.py def signup() to always return False
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(signup_form, self).__init__(*args, **kwargs)

class PostForm(Form):
    title = TextField('Title')
    body = TextField('Body')
