__author__ = 'cruor'
from flask import *
from flask.ext.login import logout_user, login_required
from app import app, db
from config import ADMINS
from forms import *
from models import *
from functools import wraps
from decorators import async
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
from emails import send_email
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(basedir, 'tmp')
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
ALLOWED_EXTENSIONS = set(['zip'])


service = PayEx(merchant_number='XXXXXXXX', encryption_key='XXXXXXXXXXXXXXXX', production=False)


#Catches internal server errors
#redirects to index with original flash message intact
@app.errorhandler(500)
def internal_server(error):
    flash('Something went wrong, please report it to an administrator!')
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
            flash('You are not an administrator and do not have access to this.')
            return redirect(url_for('index'))
    return wrap


#Test for existence of premium in session
def premium_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'premium' in session:
            user = User.query.filter_by(cust_id=session['userid']).first()
            exorderl = ''
            exorder = ''
            if user.cust_notes is not None:
                exorder = Order.query.filter_by(orderident=user.cust_notes).first()
                exorderl = Orderline.query.filter_by(order_id=exorder.order_id).first()
                if exorderl.orderl_expire <= datetime.date.today() or exorderl.order_payed == "2":
                    session.pop('premium', None)
                    flash('You are not a premium user, sign up for a service before accessing this portion!')
                    return redirect(url_for('subscribe'))
                else:
                    return test(*args, **kwargs)
            else:
                return test(*args, **kwargs)
        if 'admin' in session:
            return test(*args, **kwargs)
        else:
            flash('You are not a premium user, sign up for a service before accessing this portion!')
            return redirect(url_for('subscribe'))
    return wrap


#Routes to front page, login_required during dev only
@app.route('/')
@app.route('/index')
@login_required
def index():
    newspost = Post.query.filter_by(type='newspost').order_by(Post.timestamp.desc()).first()
    newstitle = newspost.title
    newsbody = newspost.body
    servpost = Post.query.filter_by(type='service').order_by(Post.timestamp.desc()).first()
    servtitle = servpost.title
    servbody = servpost.body
    eventpost = Post.query.filter_by(type='event').order_by(Post.timestamp.desc()).first()
    eventtitle = eventpost.title
    eventbody = eventpost.body
    promopost = Post.query.filter_by(type='promo').order_by(Post.timestamp.desc()).first()
    promotitle = promopost.title
    promobody = promopost.body
    return render_template('index.html',
        title = 'Home',
        user = session['username'], newstitle=newstitle, newsbody=newsbody, servtitle=servtitle, servbody=servbody,\
        eventtitle=eventtitle, eventbody=eventbody, promobody=promobody, promotitle=promotitle)


#Routes to first step in subscription process
@app.route('/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    return render_template('subchoice.html', user=session['username'])


def genorder():
    if 'premium' in session or 'admin' in session:
        uquer = User.query.filter_by(cust_id=session['userid']).first()
        ordquer = Order(session['userid'], uquer.cust_notes)
        db.session.add(ordquer)
        db.session.commit()
    else:
        orderident = session['username']+str(random.randint(1, 2000))
        session['ordertmpholder'] = orderident
        ordquer = Order(session['userid'], orderident)
        db.session.add(ordquer)
        db.session.commit()
        session['ordertmpholder'] = orderident

#Routes to Minecraft Subscription settings regarding time periods and cost
@app.route('/mcsubscribe', methods=['GET', 'POST'])
@login_required
def mcsubscribe():
    user = session['username']
    form = SubscriptionForm()
    subtype2 = request.args.get('subtype')
    subwip = Subscription.query.filter_by(sub_type=subtype2).first()
    subname = subwip.sub_name
    subdescription = subwip.sub_description
    subtype = subwip.sub_type
    subpris = subwip.sub_pris
    if subtype2 == "MC1024":
        form.subsel.choices = [(12000, '120NOK - 1-Month'), (36000, '360NOK - 3-Month'), (72000, '720NOK - 6-Month')]
    if subtype2 == "MC2048":
        form.subsel.choices = [(22000, '220NOK - 1-Month'), (66000, '660NOK - 3-Month'), (132000, '1320NOK - 6-Month')]
    if subtype2 == "MC2560":
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
            returnUrl='http://84.49.16.101/response',
            view='CREDITCARD',
            cancelUrl='http://84.49.16.101/response'
        )
        print response
        dbprice = subprice[:-2]
        sub = Subscription.query.filter_by(sub_pris=dbprice).first()
        dbsubid = sub.sub_id
        uquer = User.query.filter_by(cust_id=session['userid']).first()
        if uquer.cust_notes is None:
            avport = Port.query.filter_by(port_used=2).first()
            stmt = update(Port).where(Port.port_id == avport.port_id).values(port_used=1)
            db.session.execute(stmt)
            genorder()
            months = calcmonths(subprice)
            orderlineorderquer = Order.query.filter_by(orderident=session['ordertmpholder']).first()
            orderlinequer = Orderline(avport.port_id, dbsubid, orderlineorderquer.order_id, datetime.date.today(),
                                      datetime.date.today() + dateutils.relativedelta(months=months), '2')
            db.session.add(orderlinequer)
            db.session.commit()
        else:
            months = calcmonths(subprice)
            orderlineorderquer = Order.query.filter_by(orderident=uquer.cust_notes).first()
            existport = Orderline.query.filter_by(order_id=orderlineorderquer.order_id).first()
            orderlinequer = Orderline(existport.port_id, dbsubid, orderlineorderquer.order_id, datetime.date.today(),
                                      existport.orderl_expire + dateutils.relativedelta(months=months), '2')
            updstmt = update(Orderline).where(Orderline.orderl_id == existport.orderl_id).values(order_payed='DELETEME')
            db.session.execute(updstmt)
            db.session.add(orderlinequer)
            db.session.commit()
        if 'premium' in session or 'admin' in session:
            stmt = update(User).where(User.cust_id==session['userid']).\
            values(role=2, cust_notes=session['ordertmpholder'])
            db.session.execute(stmt)
            db.session.commit()
            return redirect(response['redirectUrl'])
        else:
            session['premium'] = 2
            stmt = update(User).where(User.cust_id==session['userid']).\
            values(role=2, cust_notes=session['ordertmpholder'])
            db.session.execute(stmt)
            db.session.commit()
        return redirect(response['redirectUrl'])
    return render_template('subscribe.html', form=form, subname=subname, subdescription=subdescription,
                           subtype=subtype, subpris=subpris)

def calcmonths(subprice):
    if subprice == '12000' or subprice == '22000' or subprice == '29000':
        print 1
        return 1
    elif subprice == '36000' or subprice == '66000' or subprice == '87000':
        print 2
        return 3
    elif subprice == '72000' or subprice == '132000' or subprice == '174000':
        print 3
        return 6
    else:
        print "Something went wrong"

#Response handler for PayEx
@app.route('/response', methods=['GET','POST'])
@login_required
def response():
    receipt2 = request.args.get('orderRef')
    if receipt2 is not None:
        uquer = User.query.filter_by(cust_id=session['userid']).first()
        if 'ordertmpholder' in session:
            oldorder = Orderline.query.filter_by(order_payed='DELETEME').first()
            if oldorder is not None and oldorder.order_payed == 'DELETEME':

                orderlineorderquer = Order.query.filter_by(orderident=session['ordertmpholder']).first()
                order = Orderline.query.filter_by(order_id=orderlineorderquer.order_id).first()
                subid = order.sub_id
                ordid = str(order.order_id)
                ordexp = str(order.orderl_expire)
                stmt = update(Orderline).where(Orderline.orderl_id == order.orderl_id).values(order_payed='1')
                db.session.execute(stmt)

                db.session.commit()
                send_email('Din ordrereferanse fra Gameserver.no', ADMINS[0], session['email'],  "Your order reference "
                                                                                               "with Gameserver.no:\n"
                                                                                               "Sub ID: " + str(subid) + "\n"
                                                                                               "Order ID: "+str(ordid) + "\n"
                                                                                               "Order Expiration: "+ str(ordexp),
                                                                                               "Your order reference "
                                                                                               "with Gameserver.no:\n"
                                                                                               "Sub ID: " + str(subid) + "\n"
                                                                                               "Order ID: "+str(ordid) + "\n"
                                                                                               "Order Expiration: "+ str(ordexp))
                print order.order_payed+"test1"
            else:
                orderlineorderquer = Order.query.filter_by(orderident=session['ordertmpholder']).first()
                order = Orderline.query.filter_by(order_id=orderlineorderquer.order_id).first()
                subid = order.sub_id
                ordid = str(order.order_id)
                ordexp = str(order.orderl_expire)
                stmt = update(Orderline).where(Orderline.orderl_id == order.orderl_id).values(order_payed='1')
                db.session.execute(stmt)
                db.session.commit()
                send_email('Din ordrereferanse fra Gameserver.no', ADMINS[0], session['email'], "Your order reference "
                                                                                               "with Gameserver.no:\n"
                                                                                               "Sub ID: " + str(subid) + "\n"
                                                                                               "Order ID: "+str(ordid) + "\n"
                                                                                               "Order Expiration: "+ str(ordexp),
                                                                                               "Your order reference "
                                                                                               "with Gameserver.no:\n"
                                                                                               "Sub ID: " + str(subid) + "\n"
                                                                                               "Order ID: "+str(ordid) + "\n"
                                                                                               "Order Expiration: "+ str(ordexp))
                print order.order_payed+"test2"
        else:
            oldorder = Orderline.query.filter_by(order_payed='DELETEME').first()
            if oldorder is not None and oldorder.order_payed == 'DELETEME':
                orderlineorderquer = Order.query.filter_by(orderident=session['ordertmpholder']).first()
                order = Orderline.query.filter_by(order_id=orderlineorderquer.order_id).first()
                subid = order.sub_id
                ordid = str(order.order_id)
                ordexp = str(order.orderl_expire)
                stmt = update(Orderline).where(Orderline.orderl_id == order.orderl_id).values(order_payed='1')
                db.session.execute(stmt)

                db.session.commit()
                send_email('Din ordrereferanse fra Gameserver.no', ADMINS[0], session['email'], "Your order reference "
                                                                                               "with Gameserver.no:\n"
                                                                                               "Sub ID: " + str(subid) + "\n"
                                                                                               "Order ID: "+str(ordid) + "\n"
                                                                                               "Order Expiration: "+ str(ordexp),
                                                                                               "Your order reference "
                                                                                               "with Gameserver.no:\n"
                                                                                               "Sub ID: " + str(subid) + "\n"
                                                                                               "Order ID: "+str(ordid) + "\n"
                                                                                               "Order Expiration: "+ str(ordexp))
            else:
                orderlineorderquer = Order.query.filter_by(orderident=session['ordertmpholder']).first()
                order = Orderline.query.filter_by(order_id=orderlineorderquer.order_id).first()
                subid = order.sub_id
                ordid = str(order.order_id)
                ordexp = str(order.orderl_expire)
                stmt = update(Orderline).where(Orderline.orderl_id == order.orderl_id).values(order_payed='1')
                db.session.execute(stmt)
                db.session.commit()
                send_mail('Din ordrereferanse fra Gameserver.no', ADMINS[0], session['email'],  "Your order reference "
                                                                                               "with Gameserver.no:\n"
                                                                                               "Sub ID: " + str(subid) + "\n"
                                                                                               "Order ID: "+str(ordid) + "\n"
                                                                                               "Order Expiration: "+ str(ordexp),
                                                                                               "Your order reference "
                                                                                               "with Gameserver.no:\n"
                                                                                               "Sub ID: " + str(subid) + "\n"
                                                                                               "Order ID: "+str(ordid) + "\n"
                                                                                               "Order Expiration: "+ str(ordexp))
            return render_template('response.html', receipt=receipt2, subid=subid, ordid=ordid, ordexp=ordexp)
        return render_template('response.html', receipt=receipt2, subid=subid, ordid=ordid, ordexp=ordexp)
    else:
        uquer = User.query.filter_by(cust_id=session['userid']).first()
        if 'ordertmpholder' in session:
            orderlineorderquer = Order.query.filter_by(orderident=session['ordertmpholder']).first()
            order = Orderline.query.filter_by(order_id=orderlineorderquer.order_id).first()
            subid = order.sub_id
            ordid = str(order.order_id)
            ordexp = str(order.orderl_expire)
            stmt = update(Orderline).where(Orderline.orderl_id == order.orderl_id).values(order_payed='2')
            db.session.execute(stmt)
            portreset = update(Port).where(Port.port_id == order.port_id).values(port_used=2)
            uuupdate = update(User).where(User.cust_id==session['userid']).values(role='0', cust_notes=None)
            db.session.execute(uuupdate)
            db.session.execute(portreset)
            db.session.delete(order)
            db.session.commit()
            session.pop('premium', None)
            print 'Something went wrong'
            cancmes = 'Your order has been terminated'
            return render_template('response.html', receipt=cancmes)

        else:
            orderlineorderquer = Order.query.filter_by(orderident=uquer.cust_notes).first()
            order = Orderline.query.filter_by(order_id=orderlineorderquer.order_id).first()
            subid = order.sub_id
            ordid = str(order.order_id)
            ordexp = str(order.orderl_expire)
            stmt = update(Orderline).where(orderl_id == order.orderl_id).values(order_payed='2')
            db.session.execute(stmt)
            portreset = update(Port).where(port_id == order.port_id).values(port_used=2)
            uuupdate = update(User).where(User.cust_id==session['userid']).values(role='0', cust_notes=None)
            db.session.execute(uuupdate)
            db.session.delete(order)
            db.session.commit()
            session.pop('premium', None)
            cancmes = 'Your order has been terminated'
            return render_template('response.html', receipt=cancmes)


#Gavekort handtering
@app.route('/gccreate', methods=['GET', 'POST'])
@login_required
@admin_required
def gccreate():
    #sub_id, gift_code, expiration, in_use
    form = GiftCardForm()
    gcs = Giftcard.query.all()
    if request.method == 'POST' and request.form['submit'] == 'Generate Giftcard':
        gquer = Giftcard(form.sub_id.data, form.gift_code.data, form.expiration.data)
        db.session.add(gquer)
        db.session.commit()
    return render_template('gccreate.html', form=form, gcs=gcs)

@app.route('/gccheck', methods=['GET', 'POST'])
@login_required
def gccheck():
    form = GiftCardCheckin()
    if request.method == 'POST':
        gc = Giftcard.query.filter_by(gift_code=form.giftcode.data).first()
        sub = Subscription.query.filter_by(sub_id=gc.sub_id).first()
        avport = Port.query.filter_by(port_used=2).first()
        stmt = update(Port).where(Port.port_id == avport.port_id).values(port_used=1)
        db.session.execute(stmt)
        gcstm = update(Giftcard).where(Giftcard.gift_code==gc.gift_code).values(in_use=True)
        db.session.execute(gcstm)
        genorder()
        months = sub.sub_mnd
        orderlineorderquer = Order.query.filter_by(orderident=session['ordertmpholder']).first()
        orderlinequer = Orderline(avport.port_id, sub.sub_id, orderlineorderquer.order_id, datetime.date.today(),
                                      datetime.date.today() + dateutils.relativedelta(months=months), '1')
        db.session.add(orderlinequer)
        db.session.commit()
    return render_template('gccheckin.html', form=form)
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



@app.route('/administrate')
@admin_required
def administrate():
    return render_template('adminchoice.html')



@app.route('/controllers')
@login_required
@premium_required
def controllers():
    return render_template('controllers.html')



@app.route('/subadmin', methods=['POST', 'GET'])
@admin_required
def subadmin():
    form = SubManageForm()
    orders = Orderline.query.filter_by(order_payed=1).all()
    if request.method == 'POST' and request.form['submit'] == 'Add Subscription':
        subquer = Subscription(form.sub_name.data, form.sub_description.data,
                               form.sub_type.data, form.sub_days.data, form.sub_hours.data, form.sub_mnd.data,
                               form.sub_limit.data, form.sub_pris.data)
        db.session.add(subquer)
        db.session.commit()
        flash('The Subscription has been added to the pool')
        return render_template('subadmin.html', form=form, orders=orders)
    if request.method == 'POST' and request.form['submit'] == 'Delete Unpayed':
        unpayedorder = Orderline.query.filter_by(order_payed='2').all()
        for unpayed in unpayedorder:
            print unpayed
            resetuser(unpayed.orderl_id)
            cleanports()
        flash('Unpayed deleted')
    if request.method == 'POST' and request.form['submit'] == 'Delete Expired':
        ordl = Orderline.query.filter_by(order_payed='1').all()
        for ordr in ordl:
            if ordr.orderl_expire + dateutils.relativedelta(months=1) <= datetime.date.today():
                resetuser(ordr.orderl_id)
                cleanports()
        flash('Expired deleted')
        return render_template('subadmin.html', form=form, orders=orders)
    return render_template('subadmin.html', form=form, orders=orders)

#cleanly purges a user and his orders from the database
def resetuser(orderlid):
    print orderlid
    delorder = Orderline.query.filter_by(orderl_id=orderlid).first()
    delorderorder = Order.query.filter_by(order_id=delorder.order_id).first()
    print delorderorder.cust_id
    usertbreset = User.query.filter_by(cust_id=delorderorder.cust_id).first()
    print usertbreset.cust_username
    upduser = update(User).where(User.cust_id == delorderorder.cust_id).values(role=0, cust_notes=None)
    db.session.execute(upduser)
    db.session.delete(delorder)
    db.session.commit()
    time.sleep(2)
    db.session.delete(delorderorder)
    db.session.commit()

#Method for cleaning out ports set to used without an attached subscription
def cleanports():
    allports = Port.query.filter_by(port_used=1).all()
    for ports in allports:
        ordl = Orderline.query.filter_by(port_id=ports.port_id).first()

        if ordl is None:
            stmt = update(Port).where(Port.port_id==ports.port_id).values(port_used=2)
            db.session.execute(stmt)
            db.session.commit()
            flash('Port '+str(ports.port_no)+ " cleaned")
        elif ordl.orderl_expire + dateutils.relativedelta(months=1) <= datetime.date.today():
            stmt = update(Port).where(Port.port_id==ports.port_id).values(port_used=2)
            db.session.execute(stmt)
            db.session.commit()
            flash('Port '+str(ports.port_no)+ " cleaned")
        else:
            flash('No port was reset')

#Administrate the service, adding servers, ports and managing them through the control panel.
@app.route('/servadmin', methods=['POST', 'GET'])
@admin_required
def servadmin():
    user = session['username']
    form = ServerForm()
    form2 = PortForm()
    form3 = UpdatePortForm()
    form4 = DeleteserverForm()
    form5 = PostForm()
    form6 = DeleteportForm()
    if request.method == 'POST' and request.form['submit'] == "Add Server":
        servname = form.servername.data
        servip = form.serverip.data
        if servname != "" and servip != "":
            oldservdb = Serverreserve.query.filter_by(server_name=servname).first()
            oldserv = ""
            if oldservdb != None:
                oldserv = oldservdb.server_name
            oldipdb = Serverreserve.query.filter_by(server_ip=servip).first()
            oldip = ""
            if oldipdb != None:
                oldip = oldipdb.server_ip
            if (str(oldserv)) != (str(servname)) and (str(oldip)) != (str(servip)):
                servquer = Serverreserve(servname, servip)
                db.session.add(servquer)
                db.session.commit()
                flash('Server Added')
            else:
                flash('Servername or IP already in use!')
        else:
            flash('Info missing')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == "Add Port":
        for form2data in form2.server.data:
            servnew = form2data.server_id
            servolddb = Port.query.filter_by(server_id=servnew).first()
            servold = ""
            if servolddb != None:
                servold = servolddb.server_id
            portnew = form2.portno.data
            portolddb = Port.query.filter_by(port_no=portnew, server_id=servnew).first()
            portold = ""
            if portolddb != None:
                portold = portolddb.port_no
            if (str(portnew) != str(portold)) or (str(servnew) != str(servold)):
                portquer = Port(form2data.server_id, form2.portno.data, form2.portused.data)
                db.session.add(portquer)
                db.session.commit()
                flash('Port '+str(portnew)+' added on Server '+str(servnew)+'!')
            else:
                flash('Port '+str(portnew)+' already in use on Server '+str(servnew)+'!')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == "Update Port":
        serverdata = form3.server.data
        serverparseid = serverdata.server_id
        stmt = update(Port).where(Port.server_id == serverparseid and Port.port_no == form3.portno.data).\
        values(port_used=form3.portused.data)
        db.session.execute(stmt)
        db.session.commit()
        flash('Port Updated')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == "Reset unused servers":
        cleanports()
        flash('Ports cleaned')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == "Delete Server":
        serverform = form4.serversel.data
        if serverform !=None:
            serverdata = serverform.server_name
            servername = Serverreserve.query.filter_by(server_name=serverdata).first()
            serverid = servername.server_id
            Port.query.filter_by(server_id=serverid).delete()
            servquerydel = Serverreserve.query.filter_by(server_id=servername.server_id).first()
            db.session.delete(servquerydel)
            db.session.commit()
            time.sleep(1)
            flash('Server deleted!')
        else:
            flash('Server already deleted!')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == "Delete Port":
        portform = form6.portsel.data
        print portform
        if portform !=None:
            #portdata = portform.port_id
            #print portdata
            portname = Port.query.filter_by(port_id=portform.port_id).delete()
            print portname
            #serverid = portname.server_id
            #Port.query.filter_by(server_id=serverid).delete()
            #Serverreserve.query.filter_by(server_name=portdata).delete()
            db.session.commit()
            time.sleep(1)
            flash('Port deleted!')
        else:
            flash('Port already deleted!')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == 'Create Newspost':
        p = Post(title=form5.title.data, body=form5.body.data, timestamp=datetime.datetime.utcnow(),
                 cust_id=session['userid'], type='newspost')
        db.session.add(p)
        db.session.commit()
    if request.method == 'POST' and request.form['submit'] == 'Create Service Announcement':
        p = Post(title=form5.title.data, body=form5.body.data, timestamp=datetime.datetime.utcnow(),
                 cust_id=session['userid'], type='service')
        db.session.add(p)
        db.session.commit()
    if request.method == 'POST' and request.form['submit'] == 'Create Event Post':
        p = Post(title=form5.title.data, body=form5.body.data, timestamp=datetime.datetime.utcnow(),
                 cust_id=session['userid'], type='event')
        db.session.add(p)
        db.session.commit()
    if request.method == 'POST' and request.form['submit'] == 'Create Promo Post':
        p = Post(title=form5.title.data, body=form5.body.data, timestamp=datetime.datetime.utcnow(),
                 cust_id=session['userid'], type='promo')
        db.session.add(p)
        db.session.commit()
    return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4, form5=form5,
                           form6=form6)


#User self-administration
@app.route('/uuadmin', methods=['GET', 'POST'])
@login_required
def uuadmin():
    form = UserinfoForm()
    custid = session['userid']
    order = Order.query.filter_by(cust_id=custid).first()
    orderlineid = Orderline.query.filter_by(order_id=order.order_id).first()
    subid = Subscription.query.filter_by(sub_id=orderlineid.sub_id).first()
    subdescription = subid.sub_description
    subtype = subid.sub_type
    subcreate = orderlineid.orderl_create
    subexpire = orderlineid.orderl_expire
    name = User.query.filter_by(cust_id=custid).first()
    email = name.cust_mail
    fname = name.cust_fname
    lname = name.cust_lname
    phone = name.cust_phone
    if request.method == 'POST' and request.form['submit'] == 'Change Info':
        oldpwd = form.oldpwd.data
        newpwd = form.pwdfield.data
        confirm = form.confirm.data
        newfname = form.fname.data
        newlname = form.lname.data
        newemail = form.email.data
        newphone = form.phone.data
        user = User.query.filter_by(cust_username=session['username']).first()
        if not (newpwd == "" and newfname == "" and newlname == "" and newemail == "" and newphone == ""):
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
            if newphone != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_phone': newphone})
                db.session.commit()
                flash('Phone number updated')
            if newemail != "":
                oldemaildb = User.query.filter_by(cust_mail=newemail).first()
                oldemail = ""
                if oldemaildb != None:
                    oldemail = oldemaildb.cust_mail
                if user.check_password(form.oldpwd.data) and oldemail == "":
                    User.query.filter_by(cust_username=user).update({'cust_mail': newemail})
                    db.session.commit()
                    flash('Email updated')
                else:
                    flash('Email already in use!')
                    return render_template('uuadmin.html', form=form)
        else:
            flash('Nothing updated')
        return render_template('uuadmin.html', form=form)
    return render_template('uuadmin.html', form=form, subdescription=subdescription, subtype=subtype,
                           subcreate=subcreate, subexpire=subexpire)


#Administrator page for user administration
@app.route('/uadmin', methods=['GET', 'POST'])
@admin_required
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
            userdelquer = db.session.query(User).filter(User.cust_username == user).first()
            db.session.delete(userdelquer)
            db.session.commit()
            time.sleep(1)
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
@app.route('/mcoutput', methods=['POST', 'GET'])
def mcoutput():
    order = Order.query.filter_by(cust_id=session['userid']).first()
    orderline = Orderline.query.filter_by(order_id=order.order_id).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    port = dbport.port_no
    serv = Server()
    user = session['username']
    output = serv.readconsole(serverip, user)
    if request.method == 'POST':
        output = serv.readconsole(serverip, user)
        return render_template('mcoutput.html', output=output)
    return render_template('mcoutput.html', output=output)


#Manage server properties output
@app.route('/servpropout')
def servpropout():
    userquer = User.query.filter_by(cust_id=session['userid']).first()
    orderquer = Order.query.filter_by(cust_id=session['userid']).first()
    orderlinequer = Orderline.query.filter_by(order_id=orderquer.order_id).first()
    port = Port.query.filter_by(port_id=orderlinequer.port_id).first()
    server = Serverreserve.query.filter_by(server_id=port.server_id).first()
    serverip = server.server_ip
    serv = Server()
    user = session['username']
    output = serv.readproperties(serverip, user)
    time.sleep(1)
    return render_template('servpropout.html', output=output)


#Show serverstatus
@app.route('/servstatus')
def servstatus():
    userquer = User.query.filter_by(cust_id=session['userid']).first()
    orderquer = Order.query.filter_by(cust_id=session['userid']).first()
    orderlinequer = Orderline.query.filter_by(order_id=orderquer.order_id).first()
    port = Port.query.filter_by(port_id=orderlinequer.port_id).first()
    server = Serverreserve.query.filter_by(server_id=port.server_id).first()
    serverip = server.server_ip
    serv = Server()
    user = session['username']
    status = serv.serverstatus(serverip, user)
    time.sleep(1)
    return render_template('servstatus.html', status=status)


#Serveradmin port output
@app.route('/servoutput')
def servoutput():
    servusequer = Serverreserve.query.all()
    servq = servusequer
    time.sleep(1)
    return render_template('servoutput.html', servq=servq)


#Serveradmin port output
@app.route('/portoutput')
def portoutput():
    portusequer = Port.query.filter_by(port_used=1).all()
    ports = portusequer
    time.sleep(1)
    return render_template('portoutput.html', ports=ports)


#Servadmin port output
@app.route('/portoutput2')
def portoutput2():
    portusequer = Port.query.filter_by(port_used=2).all()
    ports = portusequer
    time.sleep(1)
    return render_template('portoutput2.html', ports=ports)


#Servadmin delete server
#@app.route('/deleteserver', methods=['GET', 'POST'])
#def deleteserver():
#    form4 = DeleteserverForm()
#    time.sleep(1)
#    return render_template('deleteserver.html', form4=form4)


@app.route('/userinfo')
def userinfo():
    custid = session['userid']
    #order = Order.query.filter_by(cust_id=custid).first()
    #orderlineid = Orderline.query.filter_by(order_id=order.order_id).first()
    #subid = Subscription.query.filter_by(sub_id=orderlineid.sub_id).first()
    #subdescription = subid.sub_description
    #subtype = subid.sub_type
    #subcreate = orderlineid.orderl_create
    #subexpire = orderlineid.orderl_expire
    name = User.query.filter_by(cust_id=custid).first()
    email = name.cust_mail
    fname = name.cust_fname
    lname = name.cust_lname
    phone = name.cust_phone
    time.sleep(1)
    return render_template('userinfo.html', email=email, fname=fname, lname=lname, phone=phone)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    cust_mail = form.email.data
    user = User.query.filter_by(cust_username='Cruor').first()
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
            if form.email.data == usermail.cust_mail and usermail.check_password(form.password.data):
                session['remember_me'] = form.remember_me.data
                session['logged_in'] = True
                session['username'] = usermail.cust_username
                session['email'] = usermail.cust_mail
                session['userid'] = usermail.cust_id
                session['ordertmpholder'] = usermail.cust_notes
                if usermail.role == 2:
                    session['premium'] = usermail.role
                if usermail.role == 1:
                    session['admin'] = usermail.role
                if usermail.role != 1:
                    session['normal'] = usermail.role
                return redirect(url_for('index'))
            else:
                flash('Incorrect username or password')
                return render_template('login.html', title='Sign In', form=form)
        if user is not None:
            print user.cust_username
            if form.email.data == user.cust_username and user.check_password(form.password.data):
                session['remember_me'] = form.remember_me.data
                session['logged_in'] = True
                session['username'] = user.cust_username
                session['email'] = user.cust_mail
                session['userid'] = user.cust_id
                session['ordertmpholder'] = user.cust_notes
                if user.role == 2:
                    session['premium'] = user.role
                if user.role == 1:
                    session['admin'] = user.role
                    session.pop('normal', None)
                if user.role != 1:
                    session['normal'] = user.role
                return redirect(url_for('index'))
            else:
                flash('Incorrect username or password')
                return render_template('login.html', title='Sign In', form=form)
        else:
            flash('Incorrect username or password')
    return render_template('login.html', title='Sign In', form=form)


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
                    if not re.search(r'[\s]', newuser):
                        user = User(form.username.data, form.password.data, form.email.data, form.fname.data,
                               form.lname.data, form.phone.data)
                        db.session.add(user)
                        db.session.commit()
                        flash('Thanks for registering!')
                        send_email('Velkommen til Gameserver.no!', ADMINS[0], form.email.data, 'Velkommen til Gameserver.no'
                            'Her er din brukerinfo: ' + form.username.data+ form.password.data+ form.email.data+
                                                                                              form.fname.data+
                                                                                              form.lname.data+
                                                                                              form.phone.data,
                                  'Velkommen til Gameserver.no'
                            'Her er din brukerinfo: ' + form.username.data+ form.password.data+ form.email.data+
                                                                                              form.fname.data+
                                                                                              form.lname.data+
                                                                                              form.phone.data,)
                        return redirect(url_for('login'))
                    else:
                        flash('Username cannot contain whitespace!')
                        return render_template('signup.html', form=form)
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

#handles file transfer from temporary storage to final location
@async
def transfer_file(filename, user, serverip, port, ordertypeclean, stripped):
    serv = Server()
    print serverip
    serv.servercreate(str(serverip), user, str(port))
    serv.sendfile(serverip, filename, user)
    serv.unzip(serverip, user, filename)
    serv.servercreate(str(serverip), user, str(port))
    serv.editproperties(serverip, user, 'mscs-server-jar', stripped)
    serv.editproperties(serverip, user, 'mscs-server-location', '/home/minecraft/worlds/'+user)
    os.remove(os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], filename)))
    serv.editproperties(serverip, user, 'mscs-initial-memory', '128M')
    serv.editproperties(serverip, user, 'mscs-maximum-memory', ordertypeclean+'M')
    serv.editproperties(serverip, user, 'server-port', port)


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
    port = dbport.port_no
    currsub = Subscription.query.filter_by(sub_id=orderline.sub_id).first()
    ordertype = currsub.sub_type
    ordertypeclean = ordertype[2:]
    print ordertypeclean
    if request.method == 'POST':
        if request.form['submit'] == 'Generate properties':
            serv.servercreate(str(serverip), user, str(port))
            time.sleep(1)
            serv.editproperties(serverip, user, 'mscs-initial-memory', '128M')
            serv.editproperties(serverip, user, 'mscs-maximum-memory', ordertypeclean+'M')
            flash("Properties Generated")
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        if request.form['submit'] == 'Change Properties' and form.props.data != 'server-port' and \
                        form.props.data != 'mscs-initial-memory' and form.props.data != 'mscs-maximum-memory':
            key = form.props.data
            value = form.value.data
            serv.editproperties(serverip, user, key, value)
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        if request.form['submit'] == 'Change Properties' and form.props.data == 'server-port':
            flash('You are not entitled to change your server port. This is to prevent conflicting ports with other users')
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        elif request.form['submit'] == 'Change Properties' and form.props.data == 'mscs-initial-memory':
            flash('You are not entitled to change your server memory')
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        elif request.form['submit'] == 'Change Properties' and form.props.data == 'mscs-maximum-memory':
            flash('You are not entitled to change your server memory')
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        if request.form['submit'] == 'Delete Server Content':
            serv.deleteserv(serverip, user)
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        if request.form['submit'] == 'Upload Zip':
            zipfile = request.files['file']
            upload_file(zipfile)
            filenameplaceholder = zipfile.filename
            if filenameplaceholder != "":
                filenamestripped = filenameplaceholder.strip('.zip') + '.jar'
                servername = filenamestripped
                transfer_file(zipfile.filename, user, serverip, port, ordertypeclean, servername)
                flash('You did it!')
            else:
                flash('Select a file!')
        if request.form['submit'] == 'Restore From Backup':
            serv.restorebackup(serverip, user)
            flash('Server Restored')
        if request.form['submit'] == 'Backup Server':
            serv.backupserv(serverip, user)
            flash('Server Backed Up')
    return render_template('manage.html', user = session['username'], email = session['email'],
                           form=form, serverip=serverip, port=port)




#Logs the user out
@app.route('/logout')
def logout():
    logout_user()
    session.pop('logged_in', None)
    session.pop('admin', None)
    session.pop('premium', None)
    session.pop('remember_me', None)
    session.pop('ordertmpholder', None)
    session.pop('normal', None)
    return redirect(url_for('index'))