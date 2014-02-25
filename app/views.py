__author__ = 'cruor'
from flask import *
#from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm
from forms import signup_form
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
    user = session['email']
    serv = Server()

    if request.method == 'POST':
        command = request.form([])
        #if command == 'start':
        print "command worked" + command.content
        serv.serverstart(user)
        #output = serv.serverread(user)
        return render_template('server.html', output=output)
    return render_template('server.html')



@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    email = form.email.data
    user = User.query.filter_by(email=email).first()
    if form.validate_on_submit():
        print form.email.data
        print user.email
        print user.nickname
        print user.role
        print user.check_password(form.password.data)
        if form.email.data == user.email and user.check_password(form.password.data):
            session['remember_me'] = form.remember_me.data
            session['logged_in'] = True
            session['username'] = user.nickname
            session['email'] = user.email
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
            user = User(form.username.data, form.password.data, form.email.data)
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

    return render_template('manage.html')


@app.route('/logout')
def logout():
    logout_user()
    session.pop('logged_in', None)
    return redirect(url_for('index'))


