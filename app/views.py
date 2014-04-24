__author__ = 'cruor'
from flask import *
from flask.ext.login import logout_user, login_required
from app import app, db
from forms import *
from models import *
from functools import wraps
from server import Server
from werkzeug import generate_password_hash
import time
from payex.service import PayEx
import random
import os
from werkzeug.utils import secure_filename
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(basedir, 'tmp')
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
ALLOWED_EXTENSIONS = set(['zip'])


service = PayEx(merchant_number='60019118', encryption_key='FYnYJJ2uJeq24p2tKTNv', production=False)


#Catches internal server errors
#redirects to index with original flash message intact
@app.errorhandler(500)
def internal_server(error):
    flash('You did something wrong')
    return render_template('index.html', user=session['username'], errmes='You were sent here because something might have gone wrong, please check your flashed message')


#Test for existence of login in session
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


#Test for existence of admin in session
def admin_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'admin' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to be an administrator to view this page.')
            return redirect(url_for('index'))
        return wrap


#Test for existence of premium in session
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


#Routes to front page, login_required during dev only
@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html',
        title = 'Home',
        user = session['username'])


#Routes to first step in subscription process
@app.route('/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    return render_template('subchoice.html', user=session['username'])


#Routes to Minecraft Subscription Options
@app.route('/mcsubopt', methods=['GET', 'POST'])
@login_required
def mcsubopt():
    return render_template('mcsubopt.html', user=session['username'])


#Routes to Minecraft Subscription settings regarding time periods and cost
@app.route('/mcsubscribe', methods=['GET', 'POST'])
@login_required
def mcsubscribe():
    user = session['username']
    form = SubscriptionForm()
    subtype2 = request.args.get('subtype')
    if subtype2 == "1":
        form.subsel.choices = [(10000, '1-Month'), (20000, '3-Month'), (30000, '6-Month')]
    if subtype2 == "2":
        form.subsel.choices = [(15000, '1-Month'), (25000, '3-Month'), (35000, '6-Month')]
    if subtype2 == "vent1":
        form.subsel.choices = [(3300, '10 slots')]
    if request.method == 'POST':
        subprice = form.subsel.data
        response = service.initialize(
            purchaseOperation='SALE',
            price=subprice,
            currency='NOK',
            vat='2500',
            orderID=session['userid']+random.getrandbits(session['userid']),
            productNumber='Server Hosting of type: '+subtype2,
            description=u'Gameserver rental host for: '+user,
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


#Response handler for PayEx
@app.route('/response', methods=['GET','POST'])
@login_required
def response():
    receipt2 = request.args.get('orderRef')
    if receipt2 is not None:
        print "This is a test"
        return render_template('response.html', receipt=receipt2)
    else:
        cancmes = 'Your order has been terminated'
        return render_template('response.html', receipt=cancmes)
    return render_template('response.html', receipt=receipt2)

def deployvent():
    user = session['username']
    serv=Server()
    serv.sendvent('80', user)
    serv.deployvent(user, 'ventpro.zip')

@app.route('/vtserver', methods=['GET', 'POST'])
@login_required
@premium_required
def vtserver():
    form = VtEditForm()
    user = session['username']
    serv=Server()
    props = serv.readventprops('80', user)
    if request.method == 'POST':
        if request.form['submit'] == 'Generate Vent':
            serv.sendvent('80', user)
            serv.deployvent(user, 'ventpro.zip', '80')
            flash('Server Deployed')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Start Server':
            serv.startvent('80', user)
            flash('Server Started')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Stop Server':
            serv.stopvent('80', user)
            flash('Server Stopped')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Restart Server':
            serv.stopvent('80', user)
            time.sleep(2)
            serv.startvent('80', user)
            flash('Server Restarting')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Edit Property':
            print form.key.data
            print form.value.data
            serv.editventprops('80', user, form.key.data, form.value.data)
    return render_template('vtserver.html', form=form, props=props)


#Minecraft Server control panel module
@app.route('/mcserver', methods=['GET', 'POST'])
@login_required
@premium_required
def mcserver():
    form = CommandForm()
    user = session['username']
    serv = Server()
    if request.method == 'POST':
        if request.form['submit'] == 'Start Server':
            serv.serverstart(user)
        if request.form['submit'] == 'Stop Server':
            serv.serverstop(user)
        if request.form['submit'] == 'stopall':
            serv.serverstop("")
        if request.form['submit'] == 'startall':
            serv.serverstart("")
        if request.form['submit'] == 'Send Command':
            command = form.command.data
            serv.servercommand(user,command)
    return render_template('server.html', form=form)


@admin_required
@app.route('/servadmin', methods=['POST', 'GET'])
def servadmin():
    user = session['username']
    form = ServerForm()
    form2 = PortForm()
    form3 = UpdatePortForm()
    form4 = DeleteserverForm()
    portusequer = Port.query.filter_by(port_used=1).all()
    ports = portusequer
    if request.method == 'POST' and request.form['submit'] == "Add Server":
        servname = form.servername.data
        servip = form.serverip.data
        if servname != "" and servip != "":
            servquer = Serverreserve(servname, servip)
            db.session.add(servquer)
            db.session.commit()
            flash('Server Added')
        else:
            flash('Info missing')

            #if newfname != "" and user.check_password(form.oldpwd.data):
                #User.query.filter_by(cust_username=user).update({'cust_fname': newfname})
                #db.session.commit()
                #flash('First Name updated')

        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user, ports=ports)
    if request.method == 'POST' and request.form['submit'] == "Add Port":
        for form2data in form2.server.data:
            serverid = Serverreserve.query.filter_by(server_name=form2data).first()
            portquer = Port(serverid.server_id, form2.portno.data, form2.portused.data)
            db.session.add(portquer)
            db.session.commit()
        flash('Port Added')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user, ports=ports)
    if request.method == 'POST' and request.form['submit'] == "Update Port":
        serverid = Serverreserve.query.filter_by(server_name=form3.data).first()
        upportquer = Port(serverid.server_id, form3.portno.data, form2.portused.data)
        db.session.add(upportquer)
        db.session.commit()
        flash('Port Updated')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user, ports=ports)
    if request.method == 'POST' and request.form['submit'] == "Delete Server":
        server = form4.serversel.data
        Serverreserve.query.filter_by(server_name=server).delete()
        db.session.commit()
        flash('Server deleted')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user, ports=ports)
    return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user, ports=ports)


#User self-administration
@app.route('/uuadmin', methods=['GET', 'POST'])
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
            if oldpwd == "":
                flash('Enter current password')
            if newpwd != "" and newpwd == confirm and user.check_password(form.oldpwd.data):
                pwdhashed = generate_password_hash(newpwd)
                User.query.filter_by(cust_username=user).update({'pwdhash': pwdhashed})
                db.session.commit()
                flash('Password updated')
            if newfname != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_fname': newfname})
                db.session.commit()
                flash('First Name updated')
            if newlname != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_lname': newlname})
                db.session.commit()
                flash('Last Name updated')
            if newemail != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_mail': newemail})
                db.session.commit()
                flash('Email updated')
            if newphone != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_phone': newphone})
                db.session.commit()
                flash('Phone number updated')
            return render_template('uuadmin.html', form=form)
        else:
            return render_template('uuadmin.html', form=form)
    return render_template('uuadmin.html', form=form)


#Administrator page for user administration
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
                db.session.commit()
                flash('Password updated, please inform the user')
            if newuname != "":
                User.query.filter_by(cust_username=user).update({'cust_username': newuname})
                db.session.commit()
                flash('Username updated, please inform the user')
            if newfname != "":
                User.query.filter_by(cust_username=user).update({'cust_fname': newfname})
                db.session.commit()
                flash('First Name updated, please inform the user')
            if newlname != "":
                User.query.filter_by(cust_username=user).update({'cust_lname': newlname})
                db.session.commit()
                flash('Last Name updated, please inform the user')
            if newemail != "":
                User.query.filter_by(cust_username=user).update({'cust_mail': newemail})
                db.session.commit()
                flash('Email updated, please inform the user')
            if newphone != "":
                User.query.filter_by(cust_username=user).update({'cust_phone': newphone})
                db.session.commit()
                flash('Phone number updated, please inform the user')
            if newnote != "":
                User.query.filter_by(cust_username=user).update({'cust_notes': newnote})
                db.session.commit()
                flash('Note updated, please inform the user')
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)
        else:
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)
    return render_template('uadmin.html', form=form, form2=form2, form3=form3)


#Helper for the minecraft output frame
@app.route('/mcoutput')
def mcoutput():
    serv = Server()
    user = session['username']
    output = serv.readconsole(user)
    return render_template('mcoutput.html', output=output)


#Routes to login for users
@app.route('/servpropout')
def servpropout():
    serv = Server()
    user = session['username']
    output = serv.readproperties(user)
    time.sleep(1)
    return render_template('servpropout.html', output=output)

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
                session['userid'] = usermail.cust_id
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
                session['userid'] = user.cust_id
                if user.role == 3:
                    session['premium'] = user.role
                if user.role == 2:
                    session['admin'] = user.role
                return redirect(url_for('index'))
        else:
            flash('Something went wrong, Email or Password might be wrong')
    return render_template('login.html', title = 'Sign In', form = form)


#Routes to signup for new users
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = signup_form(request.form)
    if request.method == 'POST':
        if form.validate() and form.phone.data.isdigit():
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


#checks for allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


#handles file uploading to the temporary directory
def upload_file(rfile):
    zipfile = rfile
    if zipfile and allowed_file(zipfile.filename):
        filename = secure_filename(zipfile.filename)
        zipfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File Uploaded Successfully')


#Routes to your server management control panel
@app.route('/manage', methods=['GET', 'POST'])
@premium_required
def manage():
    user = session['username']
    serv = Server()
    properties = serv.readproperties(user)
    form = PropertiesForm()
    if request.method == 'POST':
        if request.form['submit'] == 'servCreate':
            server = request.form['server']
            port = request.form['port']
            serv = Server()
            user = session['username']
            serv.servercreate(server, user, port)
            return render_template('manage.html',
                                   user = session['username'],
                                   properties=properties,
                                   email = session['email'],
                                   form = form)
        if request.form['submit'] == 'Change Properties' and form.props.data != 'server-port':
            key = form.props.data
            value = form.value.data
            serv.editproperties(user, key, value)
            return render_template('manage.html',
                                   user = session['username'],
                                   properties=properties,
                                   email = session['email'],
                                   form = form)
        elif request.form['submit'] == 'Change Properties' and form.props.data == 'server-port':
            flash('You are not entitled to change your server port. This is to prevent conflicting ports with other users')
            return render_template('manage.html',
                                   user = session['username'],
                                   properties=properties,
                                   email = session['email'],
                                   form = form)
        if request.form['submit'] == 'Delete Server Content':
            serv.deleteserv(user)
            return render_template('manage.html',
                                   user = session['username'],
                                   properties=properties,
                                   email = session['email'],
                                   form = form)
        if request.form['submit'] == 'Upload Zip':
            zipfile = request.files['file']
            upload_file(zipfile)
            filenameplaceholder = zipfile.filename
            if filenameplaceholder != "":
                filenamestripped = filenameplaceholder.strip('.zip') + '.jar'
                servername = filenamestripped
                serv.sendfile('80', zipfile.filename, user)
                serv.unzip(user, zipfile.filename)
                serv.editproperties(user, 'mscs-server-jar', servername)
                serv.editproperties(user, 'mscs-server-location', '/home/minecraft/worlds/'+user)
                os.remove(os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], zipfile.filename)))
                flash('You did it!')
            else:
                flash('Select a file!')
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


#Logs the user out
@app.route('/logout')
def logout():
    logout_user()
    session.pop('logged_in', None)
    session.pop('admin', None)
    return redirect(url_for('index'))


