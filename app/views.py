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
import datetime
import dateutils
import re
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
    return render_template('index.html', user=session['username'], errmes=error)


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

def genorder():
    orderident = session['username']+str(random.randint(1, 2000))
    session['ordertmpholder'] = orderident
    ordquer = Order(session['userid'], orderident)
    db.session.add(ordquer)
    db.session.commit()

#Routes to Minecraft Subscription settings regarding time periods and cost
@app.route('/mcsubscribe', methods=['GET', 'POST'])
@login_required
def mcsubscribe():
    user = session['username']
    form = SubscriptionForm()
    subtype2 = request.args.get('subtype')
    if subtype2 == "Small":
        form.subsel.choices = [(12000, '120NOK - 1-Month'), (36000, '360NOK - 3-Month'), (72000, '720NOK - 6-Month')]
    if subtype2 == "Medium":
        form.subsel.choices = [(22000, '220NOK - 1-Month'), (66000, '660NOK - 3-Month'), (132000, '1320NOK - 6-Month')]
    if subtype2 == "Large":
        form.subsel.choices = [(29000, '290NOK - 1-Month'), (87000, '870NOK - 3-Month'), (174000, '1740NOK - 6-Month')]
    if subtype2 == "Ventrilo":
        form.subsel.choices = [(3300, '33NOK - 10 slots'), (5800, '58NOK - 20 slots'), (8300, '83NOK - 30 slots')]
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
            #additionalValues='PAYMENTMENU=TRUE',
            returnUrl='http://127.0.0.1:5000/response',
            view='CREDITCARD',
            cancelUrl='http://127.0.0.1:5000/response'
        )
        dbprice = subprice[:-2]
        sub = Subscription.query.filter_by(sub_pris=dbprice).first()
        dbsubid = sub.sub_id
        avport = Port.query.filter_by(port_used=2).first()
        genorder()
        orderlineorderquer = Order.query.filter_by(orderident=session['ordertmpholder']).first()
        orderlinequer = Orderline(avport.port_id, dbsubid, orderlineorderquer.order_id, datetime.date.today(), datetime.date.today() + dateutils.relativedelta(months=1))
        db.session.add(orderlinequer)
        db.session.commit()
        session['premium'] = 2
        stmt = update(User).where(User.cust_id==session['userid']).\
        values(role=2)
        db.session.execute(stmt)
        db.session.commit()
        return redirect(response['redirectUrl'])
    return render_template('subscribe.html', form=form)


#Response handler for PayEx
@app.route('/response', methods=['GET','POST'])
@login_required
def response():
    receipt2 = request.args.get('orderRef')
    if receipt2 is not None:
        orderlineorderquer = Order.query.filter_by(orderident=session['ordertmpholder']).first()
        order = Orderline.query.filter_by(order_id=orderlineorderquer.order_id).first()
        subid = order.sub_id
        ordid = order.order_id
        ordexp = order.orderl_expire
        return render_template('response.html', receipt=receipt2, subid=subid, ordid=ordid, ordexp=ordexp)
    else:
        cancmes = 'Your order has been terminated'
        return render_template('response.html', receipt=cancmes)
    return render_template('response.html', receipt=receipt2)


@app.route('/vtserver', methods=['GET', 'POST'])
@login_required
@premium_required
def vtserver():
    form = VtEditForm()
    user = session['username']
    serv=Server()
    order = Order.query.filter_by(orderident=session['ordertmpholder']).first()
    orderline = Orderline.query.filter_by(order_id=order.order_id).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    port = dbport.port_no
    props = serv.readventprops(serverip, user)
    if request.method == 'POST':
        if request.form['submit'] == 'Generate Vent':
            serv.sendvent(serverip, user)
            serv.deployvent(user, 'ventpro.zip', serverip)
            flash('Server Deployed')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Start Server':
            serv.startvent(serverip, user)
            flash('Server Started')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Stop Server':
            serv.stopvent(serverip, user)
            flash('Server Stopped')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Restart Server':
            serv.stopvent(serverip, user)
            time.sleep(2)
            serv.startvent(serverip, user)
            flash('Server Restarting')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Edit Property':
            print form.key.data
            print form.value.data
            serv.editventprops(serverip, user, form.key.data, form.value.data)
    return render_template('vtserver.html', form=form, props=props)


#Minecraft Server control panel module
@app.route('/mcserver', methods=['GET', 'POST'])
@login_required
@premium_required
def mcserver():
    form = CommandForm()
    user = session['username']
    serv = Server()
    order = Order.query.filter_by(orderident=session['ordertmpholder']).first()
    orderline = Orderline.query.filter_by(order_id=order.order_id).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    port = dbport.port_no
    if request.method == 'POST':
        if request.form['submit'] == 'Start Server':
            serv.serverstart(serverip, user)
        if request.form['submit'] == 'Stop Server':
            serv.serverstop(str(serverip), user)
        if request.form['submit'] == 'Send Command':
            command = form.command.data
            serv.servercommand(str(serverip), user, command)
    return render_template('server.html', form=form)


@admin_required
@app.route('/administrate')
def administrate():
    return render_template('adminchoice.html')

@login_required
@premium_required
@app.route('/controllers')
def controllers():
    return render_template('controllers.html')

@admin_required
@app.route('/subadmin', methods=['POST', 'GET'])
def subadmin():
    form = SubManageForm()
    if request.method == 'POST' and request.form['submit'] == 'Add Subscription':
        subquer = Subscription(form.sub_name.data, form.sub_description.data,
                               form.sub_type.data, form.sub_days.data, form.sub_hours.data, form.sub_mnd.data,
                               form.sub_limit.data, form.sub_pris.data)

        db.session.add(subquer)
        db.session.commit()
        flash('The Subscription has been added to the pool')
        return render_template('subadmin.html', form=form)
    return render_template('subadmin.html', form=form)

#Administrate the service, adding servers, ports and managing them through the control panel.
@admin_required
@app.route('/servadmin', methods=['POST', 'GET'])
def servadmin():
    user = session['username']
    form = ServerForm()
    form2 = PortForm()
    form3 = UpdatePortForm()
    form4 = DeleteserverForm()
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
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user)
    if request.method == 'POST' and request.form['submit'] == "Add Port":
        for form2data in form2.server.data:
            portquer = Port(form2data.server_id, form2.portno.data, form2.portused.data)
            db.session.add(portquer)
            db.session.commit()
            flash('Port Added')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user)
    if request.method == 'POST' and request.form['submit'] == "Update Port":
        servertest = form3.server.data
        serverparseid = servertest.server_id
        stmt = update(Port).where(Port.server_id == serverparseid and Port.port_no == form3.portno.data).\
        values(port_used=form3.portused.data)
        db.session.execute(stmt)
        db.session.commit()
        flash('Port Updated')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user)
    if request.method == 'POST' and request.form['submit'] == "Delete Server":
        server = form4.serversel.data
        server2 = server.server_name
        servername = Serverreserve.query.filter_by(server_name=server2).first()
        serverid = servername.server_id
        Port.query.filter_by(server_id=serverid).delete()
        Serverreserve.query.filter_by(server_name=server2).delete()
        db.session.commit()
        time.sleep(1)
        flash('Server deleted')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user)
    return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user)


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
            time.sleep(1)
            flash('User deleted')
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)

        #if request.method == 'POST' and request.form['submit'] == "Delete Server":
         #   server = form4.serversel.data
          #  server2 = server.server_name
           # servername = Serverreserve.query.filter_by(server_name=server2).first()
            #serverid = servername.server_id
         #   Port.query.filter_by(server_id=serverid).delete()
          #  Serverreserve.query.filter_by(server_name=server2).delete()
           # db.session.commit()
            #time.sleep(1)
            #flash('Server deleted')
        #return render_template('prodadmin.html', form=form, form2=form2, form3=form3, form4=form4, user=user)

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
    order = Order.query.filter_by(orderident=session['ordertmpholder']).first()
    print order.order_id
    orderline = Orderline.query.filter_by(order_id=order.order_id).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    port = dbport.port_no
    serv = Server()
    user = session['username']
    output = serv.readconsole(serverip, user)
    return render_template('mcoutput.html', output=output)


#Routes to login for users
@app.route('/servpropout')
def servpropout():
    order = Order.query.filter_by(orderident=session['ordertmpholder']).first()
    print order.order_id
    orderline = Orderline.query.filter_by(order_id=order.order_id).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    port = dbport.port_no
    serv = Server()
    user = session['username']
    output = serv.readproperties(serverip, user)
    time.sleep(1)
    return render_template('servpropout.html', output=output)


@app.route('/servoutput')
def servoutput():
    order = Order.query.filter_by(orderident=session['ordertmpholder']).first()
    print order.order_id
    orderline = Orderline.query.filter_by(order_id=order.order_id).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    port = dbport.port_no
    serv = Server()
    user = session['username']
    servusequer = Serverreserve.query.all()
    servq = servusequer
    time.sleep(1)
    return render_template('servoutput.html', servq=servq)


@app.route('/portoutput')
def portoutput():
    order = Order.query.filter_by(orderident=session['ordertmpholder']).first()
    print order.order_id
    orderline = Orderline.query.filter_by(order_id=order.order_id).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    port = dbport.port_no
    serv = Server()
    user = session['username']
    portusequer = Port.query.filter_by(port_used=1).all()
    ports = portusequer
    time.sleep(1)
    return render_template('portoutput.html', ports=ports)


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
    if request.method == 'POST' and form.validate():
        olduser = User.query.filter_by(cust_username=form.username.data).first()
        newuser = form.username.data
        newmail = form.email.data
        oldmaildb = User.query.filter_by(cust_mail=newmail).first()
        oldmail = ""
        if oldmaildb != None:
            oldmail = oldmaildb.cust_mail
        if (str(newuser) != str(olduser)) and (str(newmail) != str(oldmail)):
            if re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", form.email.data):
                if form.phone.data == "" or form.phone.data.isdigit():
                    user = User(form.username.data, form.password.data, form.email.data, form.fname.data, form.lname.data,\
                                form.phone.data)
                    db.session.add(user)
                    db.session.commit()
                    flash('Thanks for registering!')
                    return redirect(url_for('login'))
                else:
                    flash('Phone number not valid!')
                    return render_template('signup.html', form=form)
            else:
                flash('Not a valid eMail!')
                return render_template('signup.html', form=form)
        else:
            flash('Username or eMail already exists!')
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

    form = PropertiesForm()
    order = Order.query.filter_by(orderident=session['ordertmpholder']).first()

    orderline = Orderline.query.filter_by(order_id=order.order_id).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    print serverip
    port = dbport.port_no

    if request.method == 'POST':
        if request.form['submit'] == 'Generate properties':
            serv.servercreate(str(serverip), user, str(port))
            flash("Properties Generated")
            return render_template('manage.html', user=session['username'],
                                   email=session['email'], form=form)

        if request.form['submit'] == 'Change Properties' and form.props.data != 'server-port' and form.props.data != 'max-players':
            key = form.props.data
            value = form.value.data
            serv.editproperties(serverip, user, key, value)
            return render_template('manage.html',
                                   user = session['username'],
                                   email = session['email'],form=form)

        if request.form['submit'] == 'Change Properties' and form.props.data == 'server-port':
            flash('You are not entitled to change your server port. This is to prevent conflicting ports with other users')
            return render_template('manage.html',
                                   user = session['username'],
                                   email = session['email'],form=form)

        if request.form['submit'] == 'Change Properties' and form.props.data == 'max-players':
            flash('You are not allowed to change the maximum players on your server')
            return render_template('manage.html',
                                   user = session['username'],
                                   email = session['email'],form=form)

        if request.form['submit'] == 'Delete Server Content':
            serv.deleteserv(serverip, user)
            return render_template('manage.html',
                                   user = session['username'],
                                   email = session['email'],
                                   form=form)
        if request.form['submit'] == 'Upload Zip':
            zipfile = request.files['file']
            upload_file(zipfile)
            filenameplaceholder = zipfile.filename
            if filenameplaceholder != "":
                filenamestripped = filenameplaceholder.strip('.zip') + '.jar'
                servername = filenamestripped
                serv.sendfile(serverip, zipfile.filename, user)
                serv.unzip(serverip, user, zipfile.filename)
                serv.editproperties(serverip, user, 'mscs-server-jar', servername)
                serv.editproperties(serverip, user, 'mscs-server-location', '/home/minecraft/worlds/'+user)
                os.remove(os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], zipfile.filename)))
                flash('You did it!')
            else:
                flash('Select a file!')
            return render_template('manage.html',
                           user = session['username'],
                           email = session['email'],
                           form=form)
    return render_template('manage.html',
                           user = session['username'],
                           email = session['email'],
                           form=form)


#Logs the user out
@app.route('/logout')
def logout():
    logout_user()
    session.pop('logged_in', None)
    session.pop('admin', None)
    return redirect(url_for('index'))


