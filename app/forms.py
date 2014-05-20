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
    months = DecimalRangeField(u'M\xe5neder')


class GiftCodeCheckin(Form):
    gift_code = TextField('Gavekort kode:')


class GiftCodeForm(Form):
    sub_id = QuerySelectField('Velg abonnement:', query_factory=listsub)
    gift_code = TextField('Gavekort kode:')
    expiration = DateField(u'Utl\xf8psdato: (\xC5\xC5\xC5\xC5-MM-DD)', format='%Y-%m-%d')


class ServerForm(Form):
    servername = TextField('Server navn:', validators=[validators.Required()])
    serverip = TextField('Server IP:', validators=[validators.Required()])


class PortForm(Form):
    server = QuerySelectMultipleField(u'Velg server (Hold CTRL for \xe5 velge flere servere):', query_factory=listserv)
    portno = TextField('Port:')
    portused = SelectField('Er porten i bruk:', choices=[(1, "Yes"), (2, "No")])


class UpdatePortForm(Form):
    server = QuerySelectField('Velg server:', query_factory=listserv)
    portno = TextField('Port:')
    portused = SelectField('Er porten i bruk:', choices=[(1, "Yes"), (2, "No")])


class DeleteserverForm(Form):
    serversel = QuerySelectField('Velg server:', query_factory=listserv)


class DeleteportForm(Form):
    portsel = QuerySelectField('Velg port:', query_factory=listport)


class SubManageForm(Form):
    server_id = TextField('Server ID:', validators=[validators.Required()])
    sub_name = TextField(u'Navn p\xe5 abonnementet:', validators=[validators.Required()])
    sub_description = TextField('Beskrivelse av abonnement:', validators=[validators.Required()])
    sub_type = TextField('Type abonnement:', validators=[validators.Required()])
    sub_mnd = TextField(u'Varighet i m\xe5neder:')
    sub_days = TextField('Varighet i dager:')
    sub_hours = TextField('Varighet i timer:')
    sub_limit = TextField('Begrens antall: (0 = ubegrenset)', validators=[validators.Required()])
    sub_pris = TextField('Pris for abonnement:', validators=[validators.Required()])
    sub_active = BooleanField('Aktivere abonnement:')
    sub_sms_payment = BooleanField('SMS betaling:')


class PropertiesForm(Form):
    serv = Server()
    props = TextField('Egenskap:')
    value = TextField('Verdi:')


class CommandForm(Form):
    command = TextField('Kommando:')


class UadminForm(Form):
    role = SelectField('Velg rolle:', choices=[(0, 'Standard'), (1, 'Admin'), (2, 'Premium')])
    usersel = QuerySelectField('Velg bruker:', query_factory=listallu, allow_blank=True, get_label=str)


class DeleteuserForm(Form):
    usersel = QuerySelectField('Velg bruker:', query_factory=listallu, allow_blank=True, get_label=str)


class UserinfoForm(Form):
    oldpwd = PasswordField(u'N\xe5v\xe6rende passord:', validators=[validators.Required()])
    pwdfield = PasswordField('Nytt passord:')
    confirm = PasswordField('Bekreft nytt passord:')
    email = TextField('E-post:')
    fname = TextField('Fornavn:')
    lname = TextField('Etternavn:')
    phone = TextField('Tenefonnummer:')


class AdmininfoForm(Form):
    usersel = QuerySelectField('Velg bruker:', query_factory=listallu, allow_blank=True, get_label=str)
    username = TextField('Brukernavn:')
    pwdfield = PasswordField('Passord:')
    email = TextField('E-post:')
    fname = TextField('Fornavn:')
    lname = TextField('Etternavn:')
    phone = TextField('Telefonnummer:')
    note = TextField('Notat:')


class SubscriptionForm(Form):
    subsel = RadioField('<h3>Velg abonnement:</h3>')


class LoginForm(Form):
    remember_me = BooleanField('remember_me:', default = False)
    password = PasswordField('Passord:', validators=[validators.Required()])
    email = TextField('Brukernavn eller e-post:', validators=[validators.Required()])
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(LoginForm, self).__init__(*args, **kwargs)


class VtEditForm(Form):
    key = SelectField('.ini key:', choices=[('name', 'name'), ('phonetic', 'phonetic'), ('auth', 'auth'), ('duplicates', 'duplicates'), ('adminpassword', 'adminpassword'), ('password', 'password'), ('sendbuffer', 'sendbuffer'), ('recvbuffer', 'recvbuffer'), ('diag', 'diag'), ('logontimeout', 'logontimeout'), ('closestd', 'closestd'), ('timestamp', 'timestamp'), ('pingrate', 'pingrate'), ('extrabuffer', 'extrabuffer'), ('chanwidth', 'chanwidth'), ('chandepth', 'chandepth'), ('chanclients', 'chanclients'), ('disablequit', 'diasablequit'), ('voicecodec', 'voicecodec'), ('voiceformat', 'voiceformat'), ('silentlobby', 'silentlobby'), ('autokick', 'autokick'), ('codexmaxbw', 'codexmaxbw')])
    value = TextField('Ny verdi:')


class signup_form(Form):
    username = TextField('Brukernavn:*', validators=[validators.Required()])
    password = PasswordField('Passord:*', validators=[validators.Required()])
    confirm = PasswordField('Bekreft passord:*', validators=[validators.Required(), validators.EqualTo('password', message='Passwords must match')])
    email = TextField('E-post:*', validators=[validators.Required()])
    fname = TextField('Fornavn:*', validators=[validators.Required()])
    lname = TextField('Etternavn:*', validators=[validators.Required()])
    phone = TextField('Telefonnummer: (bare tall)')
    accept_tos = BooleanField(u'Jeg aksepterer bruksvilk\xe5r:*', default = False, validators=[validators.Required()])
    #catches csrf_enabled for site security, and to prevent it from being sent for validation
    #this would force forms.validate() in views.py def signup() to always return False
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(signup_form, self).__init__(*args, **kwargs)


class PostForm(Form):
    title = TextField('Tittel:')
    body = TextField('Tekst:')
