__author__ = 'cruor'
from flask import *
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm, signup_form, UadminForm, AdmininfoForm, SubscriptionForm, PropertiesForm, UserinfoForm, DeleteuserForm, CommandForm
from models import User, ROLE_USER, ROLE_ADMIN
from functools import wraps
from server import Server
from werkzeug import generate_password_hash
import threading
import sys
import time
from payex.service import PayEx
import random

service = PayEx(merchant_number='60019118', encryption_key='FYnYJJ2uJeq24p2tKTNv', production=False)

@app.errorhandler(500)
def internal_server(error):
    flash('You did something wrong')
    return render_template('index.html')

def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        if 'admin' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to log in first.')
            return redirect(url_for('login'))
    return wrap

def admin_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'admin' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to be an administrator to view this page.')
            return redirect(url_for('index'))
        return wrap

def premium_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'premium' in session:
            return test(*args, **kwargs)
        if 'admin' in session:
            return test(*args, **kwargs)
        else:
            flash('You are not a premium user, sign up for a service before accessing this portion!')
            return redirect(url_for('login'))
    return wrap


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))




@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html',
        title = 'Home',
        user = session['username'])

def serveroutput(uname):
    serv = Server()
    returnvalue = serv.readconsole(uname)
    threading.Timer(4, serveroutput(uname))
    sys.stdout.flush()
    return returnvalue

@app.route('/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    return render_template('subchoice.html', form=form)


@app.route('/mcsubopt', methods=['GET', 'POST'])
@login_required
def mcsubopt():
    return render_template('mcsubopt.html')


@app.route('/mcsubscribe', methods=['GET', 'POST'])
@login_required
def mcsubscribe():
    user = session['username']
    form = SubscriptionForm()
    subtype2 = request.args.get('subtype')
    print subtype2
    if request.method == 'POST':
        response = service.initialize(
            purchaseOperation='SALE',
            price='1000',
            currency='NOK',
            vat='2500',
            orderID=session['userid']+random.getrandbits(session['userid']),
            productNumber='Server Hosting',
            description=u'Gameserver rental host',
            clientIPAddress='127.0.0.1',
            clientIdentifier='USERAGENT=test&username=testuser',
            additionalValues='PAYMENTMENU=TRUE',
            returnUrl='http://127.0.0.1:5000/response',
            view='PX',
            cancelUrl='http://127.0.0.1:5000/response'
        )
        print response
        return redirect(response['redirectUrl'])
    return render_template('subscribe.html', form=form)


@app.route('/response/', methods=['GET','POST'])
@login_required
def response():
    receipt2 = request.args.get('orderRef')
    if receipt2 is not None:
        return render_template('response.html', receipt=receipt2)
    else:
        cancmes = 'Your order has been terminated'
        return render_template('response.html', receipt=cancmes)
    return render_template('response.html', receipt=receipt2)


@app.route('/mcserver', methods=['GET', 'POST'])
@login_required
@premium_required
def mcserver():
    form = CommandForm()
    user = session['username']
    serv = Server()
    servoutput = serv.readconsole(user)
    output = servoutput
    if request.method == 'POST':
        if request.form['submit'] == 'Start':
            serv.serverstart(user)
            #output = serv.serverread(user)
            return render_template('server.html')
        if request.form['submit'] == 'Stop':
            serv.serverstop(user)
        if request.form['submit'] == 'stopall':
            serv.serverstop("")
        if request.form['submit'] == 'startall':
            serv.serverstart("")
        if request.form['submit'] == 'Send Command':
            command = form.command.form['Command']
            serv.servercommand(user,command)
    return render_template('server.html', form=form)

@app.route('/uuadmin', methods=['GET','POST'])
@login_required
def uuadmin():
    form = UserinfoForm()
    if request.method == 'POST':
        if request.form['submit'] == 'Change Info':
            oldpwd = form.oldpwd.data
            newpwd = form.pwdfield.data
            confirm = form.confirm.data
            newfname = form.fname.data
            newlname = form.lname.data
            newemail = form.email.data
            newphone = form.phone.data
            username = session['username']
            user = User.query.filter_by(cust_username=username).first()
            if newpwd != "" and newpwd == confirm and user.check_password(form.oldpwd.data):
                pwdhashed = generate_password_hash(newpwd)
                User.query.filter_by(cust_username=user).update({'pwdhash': pwdhashed})
                flash('Password updated, please inform the user')
            if newfname != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_fname': newfname})
                flash('First Name updated, please inform the user')
            if newlname != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_lname': newlname})
                flash('Last Name updated, please inform the user')
            if newemail != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_mail': newemail})
                flash('Email updated, please inform the user')
            if newphone != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_phone': newphone})
                flash('Phone number updated, please inform the user')
            return render_template('uuadmin.html', form=form)
        else:
            return render_template('uuadmin.html', form=form)
    return render_template('uuadmin.html', form=form)


@admin_required
@app.route('/uadmin', methods=['GET','POST'])
def uadmin():
    form = UadminForm()
    form2 = AdmininfoForm()
    form3 = DeleteuserForm()
    if request.method == 'POST':
        if request.form['submit'] == 'Change Role':
            role = form.role.data
            user = form.usersel.data
            User.query.filter_by(cust_username=user).update({'role': role})
            db.session.commit()
            flash('User updated')
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)
        if request.form['submit'] == 'Delete User':
            user = form3.usersel.data
            User.query.filter_by(cust_username=user).delete()
            db.session.commit()
            flash('User deleted')
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)
        if request.form['submit'] == 'Change Info':
            newpwd = form2.pwdfield.data
            newfname = form2.fname.data
            newlname = form2.lname.data
            newuname = form2.username.data
            newemail = form2.email.data
            newphone = form2.phone.data
            newnote = form2.note.data
            user = form2.usersel.data
            if newpwd != "":
                pwdhashed = generate_password_hash(newpwd)
                User.query.filter_by(cust_username=user).update({'pwdhash': pwdhashed})
                flash('Password updated, please inform the user')
            if newuname != "":
                User.query.filter_by(cust_username=user).update({'cust_username': newuname})
                flash('Username updated, please inform the user')
            if newfname != "":
                User.query.filter_by(cust_username=user).update({'cust_fname': newfname})
                flash('First Name updated, please inform the user')
            if newlname != "":
                User.query.filter_by(cust_username=user).update({'cust_lname': newlname})
                flash('Last Name updated, please inform the user')
            if newemail != "":
                User.query.filter_by(cust_username=user).update({'cust_mail': newemail})
                flash('Email updated, please inform the user')
            if newphone != "":
                User.query.filter_by(cust_username=user).update({'cust_phone': newphone})
                flash('Phone number updated, please inform the user')
            if newnote != "":
                User.query.filter_by(cust_username=user).update({'cust_notes': newnote})
                flash('Note updated, please inform the user')
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)
        else:
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)
    return render_template('uadmin.html', form=form, form2=form2, form3=form3)


@app.route('/mcoutput')
def mcoutput():
    serv = Server()
    user = session['username']
    output = serv.readconsole(user)
    return render_template('mcoutput.html', output=output)

import forms
@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    cust_mail = form.email.data
    user = User.query.filter_by(cust_username='Cruor').first()
    #print user
    #usermail = User.query.filter_by(cust_mail='kliknes@gmail.com').first()
    if request.method == 'POST':
        if 'kliknes@gmail.com' is not cust_mail:
            usermail = User.query.filter_by(cust_mail=cust_mail).first()
            #user = User.query.filter_by(cust_username=cust_mail).first()
            #print user
            #print usermail.cust_mail
        if 'Cruor' is not cust_mail:
            user = User.query.filter_by(cust_username=cust_mail).first()
            #print user
    if form.validate_on_submit():
        if usermail is not None:
            print usermail.cust_mail
            if form.email.data == usermail.cust_mail and usermail.check_password(form.password.data):
                session['remember_me'] = form.remember_me.data
                session['logged_in'] = True
                session['username'] = usermail.cust_username
                session['email'] = usermail.cust_mail
                if usermail.role == 3:
                    session['premium'] = usermail.role
                if usermail.role == 2:
                    session['admin'] = usermail.role
                return redirect(url_for('index'))
        if user is not None:
            print user.cust_username
            if form.email.data == user.cust_username and user.check_password(form.password.data):
                session['remember_me'] = form.remember_me.data
                session['logged_in'] = True
                session['username'] = user.cust_username
                session['email'] = user.cust_mail
                if user.role == 3:
                    session['premium'] = user.role
                if user.role == 2:
                    session['admin'] = user.role
                return redirect(url_for('index'))
        else:
            flash('Something went wrong, Email or Password might be wrong')
    return render_template('login.html',
        title = 'Sign In',
        form = form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = signup_form(request.form)
    if request.method == 'POST':
        if form.validate():
            user = User(form.username.data, form.password.data, form.email.data, form.fname.data, form.lname.data, form.phone.data)
            db.session.add(user)
            db.session.commit()
            flash('Thanks for registering')
            return redirect(url_for('login'))
        else:
            flash('Something went wrong')
            return render_template('signup.html', form=form)
    else:
        return render_template('signup.html', form=form)

@app.route('/manage', methods =['GET', 'POST'])
@premium_required
def manage():
    user = session['username']
    serv = Server()
    properties = serv.readproperties(user)
    form = PropertiesForm()
    time.sleep(2)
    if request.method == 'POST':
        if request.form['submit'] == 'servCreate':
            server = request.form['server']
            port = request.form['port']
            serv = Server()
            user = session['username']
            serv.servercreate(server,user,port)
            return render_template('manage.html',
                                   user = session['username'],
                                   properties=properties,
                                   email = session['email'],
                                   form = form)
        if request.form['submit'] == 'Change Properties':
            key = form.props.data
            value = form.value.data
            serv.editproperties(user, key, value)

            return render_template('manage.html',
                                   user = session['username'],
                                   properties=properties,
                                   email = session['email'],
                                   form = form)

    return render_template('manage.html',
                           user = session['username'],
                           properties=properties,
                           email = session['email'],
                           form = form)

@app.route('/logout')
def logout():
    logout_user()
    session.pop('logged_in', None)
    session.pop('admin', None)
    return redirect(url_for('index'))


