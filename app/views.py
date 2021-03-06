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
from threading import Thread
from cardgen import phrasegen
from werkzeug.utils import secure_filename
from emails import send_email
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(basedir, 'tmp')
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
ALLOWED_EXTENSIONS = set(['zip'])


service = PayEx(merchant_number='60019118', encryption_key='FYnYJJ2uJeq24p2tKTNv', production=False)


#Catches internal server errors
#redirects to index with original flash message intact
@app.errorhandler(500)
def internal_server(error):
    flash('Noe gikk galt, vennligst si ifra til en administrator!')
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
            flash(u'Du m\xe5 logge inn f\xf8rst!')
            return redirect(url_for('login'))
    return wrap


#Test for existence of admin in session
def admin_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'admin' in session:
            return test(*args, **kwargs)
        else:
            flash('Du er ikke en administrator, og har derfor ikke tilgang til dette!')
            return redirect(url_for('index'))
    return wrap


#Test for existence of premium in session
def premium_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'premium' in session:
            user = Order.query.filter_by(cust_id=session['userid']).first()
            ventquer = VtOrder.query.filter_by(cust_id=session['userid']).first()
            exorderl = ''
            exorder = ''
            if user.cust_id is not None:
                exorderl = Order.query.filter_by(cust_id = session['userid']).first()
                if exorderl.orderl_expire <= datetime.date.today() or exorderl.order_payed == "2":
                    session.pop('premium', None)
                    flash(u'Du er ikke en premium bruker. Registrer en tjeneste for \xe5 f\xe5 tilgang til denne delen!')
                    return redirect(url_for('subscribe'))
                else:
                    return test(*args, **kwargs)
            elif ventquer.expiration is not None:
                if ventquer.expiration <= datetime.date.today():
                    session.pop('premium', None)
                    flash(u'Du er ikke en premium bruker. Registrer en tjeneste for \xe5 f\xe5 tilgang til denne delen!')
                else:
                    return test(*args, **kwargs)
            else:
                return test(*args, **kwargs)
        if 'admin' in session:
            return test(*args, **kwargs)
        else:
            flash(u'Du er ikke en premium bruker. Registrer en tjeneste for \xe5 f\xe5 tilgang til denne delen!')
            return redirect(url_for('subscribe'))
    return wrap


#Routes to front page, login_required during dev only
@app.route('/')
@app.route('/index')
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
       newstitle=newstitle, newsbody=newsbody, servtitle=servtitle, servbody=servbody,\
        eventtitle=eventtitle, eventbody=eventbody, promobody=promobody, promotitle=promotitle)


#Routes to first step in subscription process
@app.route('/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    form = VentOrder()
    return render_template('subchoice.html', user=session['username'], form=form)

@app.route('/ventsub', methods=['GET', 'POST'])
@login_required
def ventsub():
    #TODO: Finn en bedre maate aa loese dette
    user = session['username']
    ventslots = {
        1: 10,
        2: 20,
        3: 30,
        4: 40,
        5: 50,
        6: 60,
        7: 70,
        8: 80,
        9: 90,
        10: 100,
        11: 200,
        12: 300,
        13: 400
    }
    slotprice = {
        1: '33',
        2: '58',
        3: '83',
        4: '108',
        5: '133',
        6: '158',
        7: '184',
        8: '208',
        9: '233',
        10: '258',
        11: '384',
        12: '450',
        13: '500'
}
    if request.method == 'POST' and request.form['submit'] == 'Neste Steg':
        session['slots'] = ventslots[int(request.form['slotSlider'])]
        session['months'] = request.form['monthSlider']
        totprice = int(slotprice[int(request.form['slotSlider'])])*int(session['months'])
        session['price'] = totprice
    if request.method == 'POST' and request.form['submit'] == 'Start betalingsprosessen':
        response = service.initialize(
            purchaseOperation='SALE',
            price=str(session['price'])+'00',
            currency='NOK',
            vat='2500',
            orderID=session['userid']+random.getrandbits(session['userid']),
            productNumber='Server Hosting of type: Ventrilo',
            description=u'Gameserver rental host for: '+user,
            clientIPAddress=request.remote_addr,
            clientIdentifier='USERAGENT='+request.headers.get('User-Agent')+'&username='+session['username'],
            returnUrl='http://ny.gameserver.no/vtresponse',
            view='CREDITCARD',
            cancelUrl='http://ny.gameserver.no/vtresponse'
        )
        return redirect(response['redirectUrl'])
    return render_template('ventsub.html', slots=session['slots'], price=session['price'], months=session['months'])

@app.route('/vtresponse', methods=['GET', 'POST'])
def vtresponse():
    orderref = request.args.get('orderRef')
    slots = session['slots']
    price = session['price']
    months = session['months']
    serv = Server()
    userid = session['userid']
    user = session['username']
    openport = VoicePort.query.filter_by(port_used=2).first()
    expire = datetime.date.today() + dateutils.relativedelta(months=int(months))
    existvent = VtOrder.query.filter_by(cust_id=session['userid']).first()
    if orderref is not None and existvent is not None:
        extramonths = existvent.expiration + dateutils.relativedelta(months=int(months))
        stmt = update(VtOrder).where(VtOrder.cust_id == session['userid']).values(expiration=extramonths).values(slots=slots)
        db.session.execute(stmt)
        db.session.commit()
        #server, user, key, value
        serv.editventprops(str(ventserver.server_ip), user, str("port"), str(openport.port_no))
        serv.editventprops(str(ventserver.server_ip), user, str("maxclients"), str(slots))
        send_email('Din ordrereferanse fra Gameserver.no', ADMINS[0], session['email'],
                           render_template('receiptvt.txt', subid=str(orderref),  ordexp=str(months), slots=str(slots), totprice=session['price'], orderexp=expire),
                           render_template('receiptvt.html', subid=str(orderref), ordexp=str(months), slots=str(slots), totprice=session['price'], orderexp=expire))
        return render_template('vtresponse.html', orderref=orderref, slots=slots, price=price, months=months, ordexp=expire)
    elif orderref is not None:
        vtadd = VtOrder(slots, price, expire, openport.port_id, userid)
        stmt = update(Port).where(Port.port_id == openport.port_id).values(port_used=1)
        db.session.execute(stmt)
        db.session.add(vtadd)
        db.session.commit()
        serv.sendvent(ventserver.server_ip, user)
        serv.deployvent(user, 'ventpro.zip', ventserver.server_ip)
        serv.editventprops(str(ventserver.server_ip), user, str("port"), str(openport.port_no))
        serv.editventprops(str(ventserver.server_ip), user, str("maxclients"), str(slots))
        userstm = update(User).where(User.cust_id == session['userid']).values(role=2)
        db.session.execute(userstm)
        db.session.commit()
        session['premium'] = 2
        send_email('Din ordrereferanse fra Gameserver.no', ADMINS[0], session['email'],
                           render_template('receiptvt.txt', subid=str(orderref),  ordexp=str(months), slots=str(slots), totprice=session['price'], orderexp=expire),
                           render_template('receiptvt.html', subid=str(orderref), ordexp=str(months), slots=str(slots), totprice=session['price'], orderexp=expire))
        return render_template('vtresponse.html', orderref=orderref, slots=slots, price=price, months=months, ordexp=expire)

    else:

        return render_template('vtresponse.html', orderref=orderref, slots=slots, price=price, months=months)


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
        form.subsel.choices = [(12000, u'120 NOK - 1 m\xe5ned'), (36000, u'360 NOK - 3 m\xe5neder'), (72000, u'720 NOK - 6 m\xe5neder')]
    if subtype2 == "MC2048":
        form.subsel.choices = [(22000, u'220 NOK - 1 m\xe5ned'), (66000, u'660 NOK - 3 m\xe5neder'), (132000, u'1320 NOK - 6 m\xe5neder')]
    if subtype2 == "MC2560":
        form.subsel.choices = [(29000, u'290 NOK - 1 m\xe5ned'), (87000, u'870 NOK - 3 m\xe5neder'), (174000, u'1740 NOK - 6 m\xe5neder')]
    if subtype2 == "Ventrilo":
        form.subsel.choices = [(3300, '33 NOK - 10 slots'), (5800, '58 NOK - 20 slots'), (8300, '83 NOK - 30 slots')]
    orderid = session['userid']+random.getrandbits(session['userid'])
    if request.method == 'POST':

        subprice = form.subsel.data
        response = service.initialize(
            purchaseOperation='SALE',
            price=subprice,
            currency='NOK',
            vat='2500',
            orderID=orderid,
            productNumber='Server Hosting of type: '+subtype2,
            description=u'Gameserver rental host for: '+user,
            clientIPAddress=request.remote_addr,
            clientIdentifier='USERAGENT='+request.headers.get('User-Agent')+'&username='+session['username'],
            #additionalValues='PAYMENTMENU=TRUE',
            returnUrl='http://ny.gameserver.no/response',
            view='CREDITCARD',
            cancelUrl='http://ny.gameserver.no/response'
        )
        dbprice = subprice[:-2]
        session['mcprice'] = dbprice
        session['mcmonths'] = calcmonths(subprice)
        subsid = Subscription.query.filter_by(sub_type=subtype2).first()
        session['orderid'] = orderid
        session['subid'] = subsid.sub_id
        avport = Port.query.filter_by(port_used=2).first()
        if avport.port_id is not None:
            session['portid'] = str(avport.port_id)
            return redirect(response['redirectUrl'])
    return render_template('subscribe.html', form=form, subname=subname, subdescription=subdescription,
                           subtype=subtype, subpris=subpris)


def calcmonths(subprice):
    if subprice == '12000' or subprice == '22000' or subprice == '29000':

        return 1
    elif subprice == '36000' or subprice == '66000' or subprice == '87000':

        return 3
    elif subprice == '72000' or subprice == '132000' or subprice == '174000':
        return 6
    else:
        pass
#Response handler for PayEx
@app.route('/response', methods=['GET','POST'])
@login_required
def response():
    receipt2 = request.args.get('orderRef')
    if receipt2 is not None:
        session['premium'] = 2
        subid = session['subid']
        ordid = session['orderid']
        ordercreate = datetime.date.today()
        ordexp = ordercreate + dateutils.relativedelta(months=session['mcmonths'])
        existquer = Order.query.filter_by(cust_id=session['userid']).first()
        if existquer is not None:
            updorder = update(Order).where(Order.cust_id == session['userid']).values(orderl_expire=ordexp, sub_id=int(subid), ordernumber=int(ordid))
            db.session.execute(updorder)
            db.session.commit()
            send_email('Din ordrereferanse fra Gameserver.no', ADMINS[0], session['email'],
                        render_template('receipt.txt', subid=str(subid), ordid=str(ordid), ordexp=str(ordexp), orderref=receipt2, totprice=session['mcprice']),
                        render_template('receipt.html', subid=str(subid), ordid=str(ordid), ordexp=str(ordexp), orderref=receipt2, totprice=session['mcprice']))
            return render_template('response.html', receipt=receipt2, subid=subid, totprice=session['mcprice'], ordid=ordid, ordexp=ordexp)
        else:
            order = Order(int(session['portid']), int(subid), int(ordid), ordercreate, ordexp, '1', int(session['userid']))
            db.session.add(order)
            db.session.commit()
            send_email('Din ordrereferanse fra Gameserver.no', ADMINS[0], session['email'],
                        render_template('receipt.txt', subid=str(subid), ordid=str(ordid), ordexp=str(ordexp), orderref=receipt2, totprice=session['mcprice']),
                        render_template('receipt.html', subid=str(subid), ordid=str(ordid), ordexp=str(ordexp), orderref=receipt2, totprice=session['mcprice']))
            return render_template('response.html', receipt=receipt2, subid=subid, totprice=session['mcprice'], ordid=ordid, ordexp=ordexp)
    else:
        return render_template('response.html', receipt='Din bestilling er avbrutt')        


@app.route('/gccreate', methods=['GET', 'POST'])
@login_required
@admin_required
def gccreate():
    #sub_id, gift_code, expiration, in_use
    form = GiftCodeForm()
    gcs = Giftcard.query.all()
    if request.method == 'POST' and request.form['submit'] == 'Opprett gavekort':
        giftinput = phrasegen()
        giftdb = Giftcard.query.filter_by(gift_code=giftinput).first()
        giftcode = ""
        if giftdb != None:
            giftcode = giftdb.gift_code
        if giftcode != giftinput:
            gquer = Giftcard(form.sub_id.data, giftinput, form.expiration.data)
            db.session.add(gquer)
            db.session.commit()
            flash("Gavekort generert!")
        else:
            flash("Gavekortet finnes allerede!")
        return render_template('gccreate.html', form=form, gcs=gcs)
    return render_template('gccreate.html', form=form, gcs=gcs)


@app.route('/gccheck', methods=['GET', 'POST'])
@login_required
def gccheck():
    #TODO: make this method better
    form = GiftCodeCheckin()
    #Check for the validity of the gift card code
    ##Discern the service nature
    ###Set up service - Send to Response?
    return render_template('gccheckin.html', form=form)


@app.route('/vtserver', methods=['GET', 'POST'])
@login_required
@premium_required
def vtserver():
    form = VtEditForm()
    user = session['username']
    serv = Server()
    vt = VtOrder.query.filter_by(cust_id=session['userid']).first()
    port = Port.query.filter_by(port_id=vt.port_id).first()
    server = Serverreserve.query.filter_by(server_id=port.server_id).first()
    serverip = server.server_ip
    props = serv.readventprops(serverip, user)
    if request.method == 'POST':
        if request.form['submit'] == 'Start serveren':
            serv.startvent(serverip, user)
            flash('Serveren starter!')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Stopp serveren':
            serv.stopvent(serverip, user)
            flash('Serveren stopper!')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Restart serveren':
            serv.stopvent(serverip, user)
            time.sleep(2)
            serv.startvent(serverip, user)
            flash(u'Serveren starter p\xe5 nytt!')
            return render_template('vtserver.html', form=form, props=props)
        if request.form['submit'] == 'Endre instillinger':
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
    orderline = Order.query.filter_by(cust_id=session['userid']).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    port = dbport.port_no
    if request.method == 'POST':
        if request.form['submit'] == 'Start serveren':
            ttt = Thread(target=serv.serverstart, args=(serverip, user))
            ttt.start()
            serv.serverstart(serverip, user)
        if request.form['submit'] == 'Stopp serveren':
            serv.serverstop(str(serverip), user)
        if request.form['submit'] == 'Send kommandoen':
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
    orders = Order.query.filter_by(order_payed=1).all()
    if request.method == 'POST' and request.form['submit'] == 'Legg til abonnement':
        subquer = Subscription(form.sub_name.data, form.sub_description.data,
                               form.sub_type.data, form.sub_mnd.data, form.sub_days.data, form.sub_hours.data,
                               form.sub_limit.data, form.sub_pris.data)
        db.session.add(subquer)
        db.session.commit()
        flash('Abonnementet har blitt lagt til!')
        return render_template('subadmin.html', form=form, orders=orders)
    if request.method == 'POST' and request.form['submit'] == 'Slett ubetalte abonnementer':
        unpayedorder = Order.query.filter_by(order_payed='2').all()
        for unpayed in unpayedorder:
            resetuser(unpayed.cust_id)
            cleanports()
        flash('Ubetalte abonnementer slettet!')
    if request.method == 'POST' and request.form['submit'] == u'Slett utl\xf8pte abonnementer':
        ordl = Order.query.filter_by(order_payed='1').all()
        for ordr in ordl:
            if ordr.orderl_expire + dateutils.relativedelta(months=1) <= datetime.date.today():
                resetuser(ordr.cust_id)
                cleanports()
        flash(u'Utl\xf8pte abonnementer slettet!')
        return render_template('subadmin.html', form=form, orders=orders)
    return render_template('subadmin.html', form=form, orders=orders)


#cleanly purges a user and his orders from the database
def resetuser(userid):
    delorder = Order.query.filter_by(cust_id=userid).first()
    usertbreset = User.query.filter_by(cust_id=userid).first()
    upduser = update(User).where(User.cust_id == delorder.cust_id).values(role=0, cust_notes=None)
    db.session.execute(upduser)
    db.session.delete(delorder)
    db.session.commit()


#Method for cleaning out ports set to used without an attached subscription
def cleanports():
    allports = Port.query.filter_by(port_used=1).all()
    allvoiceports = Port.query.filter_by(port_used=1).all()
    for ports in allports:
        ordl = Order.query.filter_by(port_id=ports.port_id).first()
        if ordl is None:
            stmt = update(Port).where(Port.port_id == ports.port_id).values(port_used=2)
            db.session.execute(stmt)
            db.session.commit()
            flash('Port '+str(ports.port_no)+' gjennoprettet!')
        elif ordl.orderl_expire + dateutils.relativedelta(months=1) <= datetime.date.today():
            stmt = update(Port).where(Port.port_id == ports.port_id).values(port_used=2)
            db.session.execute(stmt)
            db.session.commit()
            flash('Port '+str(ports.port_no)+' gjennoprettet!')
        else:
            flash('Ingen spillporter tilbakestillt!')
    for ports in allvoiceports:
        ordl = VtOrder.query.filter_by(port_id=ports.port_id).first()
        if ordl is None:
            stmt = update(Port).where(Port.port_id == ports.port_id).values(port_used=2)
            db.session.execute(stmt)
            db.session.commit()
            flash('Port '+str(ports.port_no)+' gjennoprettet!')
        elif ordl.orderl_expire + dateutils.relativedelta(months=1) <= datetime.date.today():
            stmt = update(Port).where(Port.port_id == ports.port_id).values(port_used=2)
            db.session.execute(stmt)
            db.session.commit()
            flash('Port '+str(ports.port_no)+' gjennoprettet!')
        else:
            flash('Ingen spillporter tilbakestillt!')


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
    if request.method == 'POST' and request.form['submit'] == "Legg til server":
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
                flash('Server lagt til!')
            else:
                flash('Server navn eller IP er allerede i bruk!')
        else:
            flash('Mangler informasjon!')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == "Legg til port":
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
                flash('Port '+str(portnew)+u' lagt til p\xe5 server '+str(servnew)+'!')
            else:
                flash('Port '+str(portnew)+u' er allerede i bruk p\xe5 server '+str(servnew)+'!')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == "Oppdatere port":
        serverdata = form3.server.data
        serverparseid = serverdata.server_id
        stmt = update(Port).where(Port.server_id == serverparseid and Port.port_no == form3.portno.data).\
        values(port_used=form3.portused.data)
        db.session.execute(stmt)
        db.session.commit()
        flash('Port oppdatert!')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == "Tilbakestill ubrukte servere":
        cleanports()
        flash('Servere tilbakestilt og porter ledige!')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == "Slett server":
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
            flash('Server slettet!')
        else:
            flash('Server allerede slettet!')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == "Slett port":
        portform = form6.portsel.data
        if portform !=None:
            portname = Port.query.filter_by(port_id=portform.port_id).delete()
            db.session.commit()
            time.sleep(1)
            flash('Port slettet!')
        else:
            flash('Port allerede slettet!')
        return render_template('prodadmin.html', form=form, form2=form2, form3=form3, user=user, form4=form4,
                               form5=form5, form6=form6)
    if request.method == 'POST' and request.form['submit'] == 'Opprette nyhetspost':
        p = Post(title=form5.title.data, body=form5.body.data, timestamp=datetime.datetime.utcnow(),
                 cust_id=session['userid'], type='newspost')
        db.session.add(p)
        db.session.commit()
    if request.method == 'POST' and request.form['submit'] == 'Opprette service melding':
        p = Post(title=form5.title.data, body=form5.body.data, timestamp=datetime.datetime.utcnow(),
                 cust_id=session['userid'], type='service')
        db.session.add(p)
        db.session.commit()
    if request.method == 'POST' and request.form['submit'] == 'Opprette hendelsespost':
        p = Post(title=form5.title.data, body=form5.body.data, timestamp=datetime.datetime.utcnow(),
                 cust_id=session['userid'], type='event')
        db.session.add(p)
        db.session.commit()
    if request.method == 'POST' and request.form['submit'] == 'Opprette kampanjepost':
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
    subid = ''
    subdescription = ''
    subtype = ''
    subcreate = ''
    subexpire = ''
    order = Order.query.filter_by(cust_id=custid).first()
    if order is not None:
        subid = Subscription.query.filter_by(sub_id=order.sub_id).first()
        subdescription = subid.sub_description
        subtype = subid.sub_type
        subcreate = order.orderl_create
        subexpire = order.orderl_expire
    name = User.query.filter_by(cust_id=custid).first()
    email = name.cust_mail
    fname = name.cust_fname
    lname = name.cust_lname
    phone = name.cust_phone
    vtquer = VtOrder.query.filter_by(cust_id=session['userid']).first()
    slots = ''
    expiration = ''
    if vtquer is not None:
        slots = vtquer.slots
        expiration = vtquer.expiration
    if request.method == 'POST' and request.form['submit'] == 'Endre informasjon':
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
                flash(u'Skriv inn n\xe5v\xe6rende passord!')
            if newpwd != "" and newpwd == confirm and user.check_password(form.oldpwd.data):
                pwdhashed = generate_password_hash(newpwd)
                User.query.filter_by(cust_username=user).update({'pwdhash': pwdhashed})
                db.session.commit()
                flash('Passord oppdatert!')
            if newfname != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_fname': newfname})
                db.session.commit()
                flash('Fornavn oppdatert!')
            if newlname != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_lname': newlname})
                db.session.commit()
                flash('Etternavn oppdatert!')
            if newphone != "" and user.check_password(form.oldpwd.data):
                User.query.filter_by(cust_username=user).update({'cust_phone': newphone})
                db.session.commit()
                flash('Telefonnummer oppdatert!')
            if newemail != "":
                oldemaildb = User.query.filter_by(cust_mail=newemail).first()
                oldemail = ""
                if oldemaildb != None:
                    oldemail = oldemaildb.cust_mail
                if user.check_password(form.oldpwd.data) and oldemail == "":
                    User.query.filter_by(cust_username=user).update({'cust_mail': newemail})
                    db.session.commit()
                    flash('E-post oppdatert!')
                else:
                    flash('E-post allerede i bruk!')
                    return render_template('uuadmin.html', form=form)
        else:
            flash('Ingenting oppdatert!')
        return render_template('uuadmin.html', form=form)
    return render_template('uuadmin.html', form=form, subdescription=subdescription, subtype=subtype,
                           subcreate=subcreate, subexpire=subexpire, slots=slots, expiration=expiration)


#Administrator page for user administration
@app.route('/uadmin', methods=['GET', 'POST'])
@admin_required
def uadmin():
    form = UadminForm()
    form2 = AdmininfoForm()
    form3 = DeleteuserForm()
    if request.method == 'POST':
        if request.form['submit'] == 'Bytt rolle':
            role = form.role.data
            user = form.usersel.data
            User.query.filter_by(cust_username=user).update({'role': role})
            db.session.commit()
            flash('Bruker oppdatert!')
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)
        if request.form['submit'] == 'Slett bruker':
            user = form3.usersel.data
            userdelquer = db.session.query(User).filter(User.cust_username == user).first()
            order = Order.query.filter_by(cust_id=userdelquer.cust_id).first()
            if order is not None:
                db.session.delete(order)
                db.session.commit()
                time.sleep(1)
            db.session.delete(userdelquer)
            db.session.commit()
            time.sleep(1)
            flash('Bruker slettet!')
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)
        if request.form['submit'] == 'Endre informasjon':
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
                flash('Passord oppdatert, vennligst informer brukeren!')
            if newuname != "":
                User.query.filter_by(cust_username=user).update({'cust_username': newuname})
                db.session.commit()
                flash('Brukernavn oppdatert, vennligst informer brukeren!')
            if newfname != "":
                User.query.filter_by(cust_username=user).update({'cust_fname': newfname})
                db.session.commit()
                flash('Fornavn oppdatert, vennligst informer brukeren!')
            if newlname != "":
                User.query.filter_by(cust_username=user).update({'cust_lname': newlname})
                db.session.commit()
                flash('Etternavn oppdatert, vennligst informer brukeren!')
            if newemail != "":
                User.query.filter_by(cust_username=user).update({'cust_mail': newemail})
                db.session.commit()
                flash('E-post oppdatert, vennligst informer brukeren!')
            if newphone != "":
                User.query.filter_by(cust_username=user).update({'cust_phone': newphone})
                db.session.commit()
                flash('Telefonnummer oppdatert, vennligst informer brukeren!')
            if newnote != "":
                User.query.filter_by(cust_username=user).update({'cust_notes': newnote})
                db.session.commit()
                flash('Notat oppdatert!')
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)
        else:
            return render_template('uadmin.html', form=form, form2=form2, form3=form3)
    return render_template('uadmin.html', form=form, form2=form2, form3=form3)


#Helper for the minecraft output frame
@app.route('/mcoutput', methods=['POST', 'GET'])
def mcoutput():
    order = Order.query.filter_by(cust_id=session['userid']).first()
    dbport = Port.query.filter_by(port_id=order.port_id).first()
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
    port = Port.query.filter_by(port_id=orderquer.port_id).first()
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
    port = Port.query.filter_by(port_id=orderquer.port_id).first()
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


@app.route('/userinfo')
def userinfo():
    custid = session['userid']
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
        if 'Cruor' is not cust_mail:
            user = User.query.filter_by(cust_username=cust_mail).first()
    if form.validate_on_submit():
        if usermail is not None:
            if form.email.data == usermail.cust_mail and usermail.check_password(form.password.data):
                session['remember_me'] = form.remember_me.data
                session['logged_in'] = True
                session['username'] = usermail.cust_username
                session['email'] = usermail.cust_mail
                session['userid'] = usermail.cust_id
                if usermail.role == 2:
                    session['premium'] = usermail.role
                if usermail.role == 1:
                    session['admin'] = usermail.role
                if usermail.role != 1:
                    session['normal'] = usermail.role
                return redirect(url_for('index'))
            else:
                flash('Feil brukernavn eller passord!')
                return render_template('login.html', title='Logg inn', form=form)
        if user is not None:
            if form.email.data == user.cust_username and user.check_password(form.password.data):
                session['remember_me'] = form.remember_me.data
                session['logged_in'] = True
                session['username'] = user.cust_username
                session['email'] = user.cust_mail
                session['userid'] = user.cust_id
                if user.role == 2:
                    session['premium'] = user.role
                if user.role == 1:
                    session['admin'] = user.role
                    session.pop('normal', None)
                if user.role != 1:
                    session['normal'] = user.role
                return redirect(url_for('index'))
            else:
                flash('Feil brukernavn eller passord!')
                return render_template('login.html', title='Logg inn', form=form)
        else:
            flash('Feil brukernavn eller passord!')
    return render_template('login.html', title='Logg inn', form=form)


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
                        flash('Takk for at du registrerte deg!')
                        send_email('Velkommen til Gameserver.no!', ADMINS[0], form.email.data,
                                   render_template('velkommen.txt', username = form.username.data,
                                                   password = form.password.data, email=form.email.data,
                                                   fname=form.fname.data, lname=form.lname.data, phone=form.phone.data),
                                  render_template('velkommen.html', username = form.username.data,
                                                   password = form.password.data, email=form.email.data,
                                                   fname=form.fname.data, lname=form.lname.data, phone=form.phone.data))
                        return redirect(url_for('login'))
                    else:
                        flash('Brukernavn kan ikke inneholde mellomrom!')
                        return render_template('signup.html', form=form)
                else:
                    flash('Telefonnummeret er ikke gyldig!')
                    return render_template('signup.html', form=form)
            else:
                flash('Ugyldig e-post!')
                return render_template('signup.html', form=form)
        else:
            flash('Brukernavn eller e-post finnes allerede!')
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
        flash('Filen er lastet opp!')


#handles file transfer from temporary storage to final location
def transfer_file(filename, user, serverip, port, ordertypeclean, stripped):
    filename = filename
    serv = Server()
    serv.servercreate(str(serverip), str(user), str(port))
    serv.sendfile(str(serverip), str(filename), str(user))
    serv.unzip(str(serverip), str(user), str(filename))
    serv.servercreate(str(serverip), str(user), str(port))
    serv.editproperties(str(serverip), str(user), 'mscs-server-jar', str(stripped))
    serv.editproperties(str(serverip), str(user), str('mscs-server-location'), str('/home/minecraft/worlds/'+user))
    os.remove(os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], filename)))
    serv.editproperties(str(serverip), user, str('mscs-initial-memory'), str('128M'))
    serv.editproperties(str(serverip), str(user), str('mscs-maximum-memory'), str(ordertypeclean+'M'))
    serv.editproperties(str(serverip), str(user), str('server-port'), str(port))


@app.route('/mcupload', methods=['GET', 'POST'])
def mcupload():
    user = session['username']
    serv = Server()
    form = PropertiesForm()
    orderline = Order.query.filter_by(cust_id=session['userid']).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    port = dbport.port_no
    currsub = Subscription.query.filter_by(sub_id=orderline.sub_id).first()
    ordertype = currsub.sub_type
    ordertypeclean = ordertype[2:]
    zipfile = request.files['thefile']
    upload_file(zipfile)
    filenameplaceholder = zipfile.filename
    filenamestripped = filenameplaceholder.strip('.zip') + '.jar'
    servername = filenamestripped
    thr = Thread(target=transfer_file, args=(filenameplaceholder, user, serverip, port, ordertypeclean, servername))
    if filenameplaceholder != "":
        #filenamestripped = filenameplaceholder.strip('.zip') + '.jar'
        #servername = filenamestripped
        thr.start()
        flash(u'Filopplastingen har startet, du vil f\xe5 en beskjed p\xe5 e-post n\xe5r den er ferdig!')
        #transfer_file(zipfile.filename, user, serverip, port, ordertypeclean, servername)
        #flash('You did it!')
    else:
        flash('Velg en fil!')
    return redirect('/manage')
#Routes to your server management control panel
@app.route('/manage', methods=['GET', 'POST'])
@premium_required
def manage():
    user = session['username']
    serv = Server()
    form = PropertiesForm()
    orderline = Order.query.filter_by(cust_id=session['userid']).first()
    dbport = Port.query.filter_by(port_id=orderline.port_id).first()
    server = Serverreserve.query.filter_by(server_id=dbport.server_id).first()
    serverip = server.server_ip
    port = dbport.port_no
    currsub = Subscription.query.filter_by(sub_id=orderline.sub_id).first()
    ordertype = currsub.sub_type
    ordertypeclean = ordertype[2:]
    if request.method == 'POST':
        if request.form['submit'] == 'Opprett properties':
            serv.servercreate(str(serverip), user, str(port))
            serv.editproperties(serverip, user, 'mscs-initial-memory', '128M')
            serv.editproperties(serverip, user, 'mscs-maximum-memory', ordertypeclean+'M')
            flash("Properties opprettet!")
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        if request.form['submit'] == 'Endre properties' and form.props.data != 'server-port' and \
                        form.props.data != 'mscs-initial-memory' and form.props.data != 'mscs-maximum-memory':
            key = form.props.data
            value = form.value.data
            serv.editproperties(serverip, user, key, value)
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        if request.form['submit'] == 'Endre properties' and form.props.data == 'server-port':
            flash(u'Du kan ikke endre din server port. Dette er for \xe5 hindre konflikt med andre servere!')
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        elif request.form['submit'] == 'Endre properties' and form.props.data == 'mscs-initial-memory':
            flash(u'Du kan ikke endre minnest\xf8rrelsen p\xe5 serveren!')
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        elif request.form['submit'] == 'Endre properties' and form.props.data == 'mscs-maximum-memory':
            flash(u'Du kan ikke endre minnest\xf8rrelsen p\xe5 serveren!')
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        if request.form['submit'] == 'Slett server innholdet':
            serv.deleteserv(serverip, user)
            return render_template('manage.html', user=session['username'], email=session['email'],
                                   form=form, serverip=serverip, port=port)
        if request.files is not None:
            zipfile = request.files['file']
            upload_file(zipfile)
            filenameplaceholder = zipfile.filename
            filenamestripped = filenameplaceholder.strip('.zip') + '.jar'
            servername = filenamestripped
            thr = Thread(target=transfer_file, args=(zipfile.filename, user, serverip, port, ordertypeclean, servername))
            if filenameplaceholder != "":
                #filenamestripped = filenameplaceholder.strip('.zip') + '.jar'
                #servername = filenamestripped
                thr.start()
                flash(u'Filopplastingen har startet, du vil f\xe5 en beskjed p\xe5 e-post n\xe5r den er ferdig!')
                #transfer_file(zipfile.filename, user, serverip, port, ordertypeclean, servername)
                #flash('You did it!')
            else:
                flash('Velg en fil!')
        if request.form['submit'] == 'Gjenopprett sikkerhetskopi':
            serv.restorebackup(serverip, user)
            flash('Serveren er gjenopprettet!')
        if request.form['submit'] == 'Sikkerhetskopier serveren':
            serv.backupserv(serverip, user)
            flash('Serveren er sikkerhetskopiert!')
    return render_template('manage.html', user=session['username'], email=session['email'],
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
