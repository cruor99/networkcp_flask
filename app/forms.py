__author__ = 'cruor'
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, PasswordField
from wtforms import validators


class LoginForm(Form):
    openid = TextField('openid', validators = [validators.Required()])
    remember_me = BooleanField('remember_me', default = False)


class signup_form(Form):
    username = TextField('Username', [validators.Required()])
    password = PasswordField('Password', [validators.Required(), validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', [validators.Required()])
    email = TextField('eMail', [validators.Required()])
    accept_tos = BooleanField('I accept the TOS', [validators.Required()])