__author__ = 'cruor'
from flask import *
#from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm
from forms import signup_form
from forms import UadminForm
from models import User, ROLE_USER, ROLE_ADMIN
from functools import wraps
from server import Server


def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
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


@app.route('/server', methods=['GET', 'POST'])
@login_required
@premium_required
def server():
    user = session['username']
    serv = Server()
    output = serv.readconsole(user)
    print output
    if request.method == 'POST':
        if request.form['submit'] == 'Start':
            serv.serverstart(user)
            #output = serv.serverread(user)
            return render_template('server.html')
        if request.form['submit'] == 'Stop':
            serv.serverstop(user)
        if request.form['submit'] == 'stopall':
            serv.serverstop(" ")
    return render_template('server.html', output=output)

@app.route('/uadmin', methods=['GET','POST'])
def uadmin():
    form = UadminForm()
    print form
    return render_template('uadmin.html', form=form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    cust_mail = form.email.data
    user = User.query.filter_by(cust_mail=cust_mail).first()
    if form.validate_on_submit():
        print form.email.data
        print user.cust_mail
        print user.cust_username
        print user.role
        print user.check_password(form.password.data)
        if form.email.data == user.cust_mail and user.check_password(form.password.data):
            session['remember_me'] = form.remember_me.data
            session['logged_in'] = True
            session['username'] = user.cust_username
            session['email'] = user.cust_mail
            if user.role == 2:
                session['premium'] = user.role
            return redirect(url_for('index'))
        else:
            flash('Something went wrong, Email or Password might be wrong')
    else:
       flash('something went wrong')# return oid.try_login(form.openid.data, ask_for = ['nickname', 'email'])
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
def manage():
    if request.method == 'POST':
        server = request.form['server']
        port = request.form['port']
        serv = Server()
        user = session['username']
        serv.servercreate(server,user,port)

    return render_template('manage.html')


@app.route('/logout')
def logout():
    logout_user()
    session.pop('logged_in', None)
    return redirect(url_for('index'))


