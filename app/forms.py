__author__ = 'cruor'
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, PasswordField
from wtforms import validators


class LoginForm(Form):
    openid = TextField('openid', validators = [validators.Required()])
    remember_me = BooleanField('remember_me', default = False)


class signup_form(Form):
    username = TextField('Username', validators=[validators.Required()])
    password = PasswordField('Password', validators=[validators.Required()])
    confirm = PasswordField('Confirm Password', validators=[validators.Required(), validators.EqualTo('confirm', message='Passwords must match')])
    email = TextField('eMail', validators=[validators.Required()])
    accept_tos = BooleanField('I accept the TOS', default = False, validators=[validators.Required()])

    #catches csrf_enabled for site security, and to prevent it from being sent for validation
    #this would force forms.validate() in views.py def signup() to always return False
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(signup_form, self).__init__(*args, **kwargs)