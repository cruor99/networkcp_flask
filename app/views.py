__author__ = 'cruor'
from flask import *
#from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm
from forms import signup_form
from models import User, ROLE_USER, ROLE_ADMIN
from functools import wraps


def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to log in first.')
            return redirect(url_for('login'))
    return wrap



@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


#@app.before_request
#def before_request():
#    g.user = current_user


#@oid.after_login
#def after_login(resp):
#    if resp.email is None or resp.email == "":
#        flash('Invalid login. Please try again.')
#        return redirect(url_for('login'))
#    user = User.query.filter_by(email = resp.email).first()
#    if user is None:
#        nickname = resp.nickname
#        if nickname is None or nickname == "":
#            nickname = resp.email.split('@')[0]
#        user = User(nickname, "123", email=resp.email,)
#        db.session.add(user)
#        db.session.commit()
#    remember_me = False
#    if 'remember_me' in session:
#        remember_me = session['remember_me']
#        session.pop('remember_me', None)
#    login_user(user, remember = remember_me)
#    return redirect(request.args.get('next') or url_for('index'))


@app.route('/')
@app.route('/index')
@login_required
def index():
    #user = g.user
    posts = [
        {
            'author': { 'nickname': 'John' },
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': { 'nickname': 'Susan' },
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html',
        title = 'Home',
#        user = user,
        posts = posts)




@app.route('/login', methods = ['GET', 'POST'])
def login():
   # if g.user is not None and g.user.is_authenticated():
   #     return redirect(url_for('index'))
    form = LoginForm()
    email = form.email.data
    user = User.query.filter_by(email=email).first()
    if form.validate_on_submit():
        print form.email.data
        print user.email
        print user.check_password(form.password.data)
        if form.email.data == user.email and user.check_password(form.password.data):
            session['remember_me'] = form.remember_me.data
            session['logged_in'] = True
            return redirect(url_for('index'))
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

@app.route('/logout')
def logout():
    logout_user()
    session.pop('logged_in', None)
    return redirect(url_for('index'))


