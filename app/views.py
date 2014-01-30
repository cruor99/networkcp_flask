__author__ = 'cruor'

from flask import *
from flask import request
from functools import wraps
from flask.ext.login import LoginManager
import os


app = Flask(__name__)
app.config.from_object('config')
app.secret_key = 'minecraft'
login_manager = LoginManager()


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    #nothing yet
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error ='Invalid login credentials'
        else:
            session['logged_in'] = True
            return redirect(url_for('welcome'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You were logged out.")
    return redirect(url_for('login'))



def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to log in first.')
            return redirect(url_for('login'))
    return wrap


@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')


@app.route('/server', methods=['GET', 'POST'])
@login_required
def servermonitor():
    error=None
    #checks to initiate server script method
    #NOT COMPLETE, ONLY TEST FOR NOW
    serv = Server()

    if request.method =='GET':
        serverinfo =serv.serverRead()
        return render_template('server.html', serverinfo=serverinfo)


    if request.method =='POST':
        serv.serverStart(mcServer)
        return render_template('server.html')

    else:
        error='Did not INIT'
    return render_template('server.html')

class Server(object):
    def __init__(self):
        self.process = False
        folder = "/home/cruor/mcServer"
    def serverStart(user):
        os.chdir("/home/cruor/"+user)
        process =subprocess.Popen("./start.sh", close_fds=True)

    def serverRead(self):
        os.chdir("/home/cruor/"+user)
       # self.process.stdout.seek(2)

    def serverStop(self):
        if self.process:
            self.serverCom("stop")
            self.process = False
            return True
        return False

    def serverCom(self, text):
        if self.process:
            self.process.stdout.seek(2)
            self.process.stdin.write("%s\n"%text)
            self.process.stdin.flush()
            self.process.stdout.flush()
            return (str(self.process.stdout.readline()), True)
        return ("", False)

    def serverPlayers(selfself):
        if self.process:
            self.serverCom("list")
            x = self.serverCom(" ")[0].split(":")[3].replace("\n","").replace(" ","")
            if x =="":
                x = 0
            else:
                x = len(x.split(","))
            return (x, self.max)
        return (0, self.max)


if __name__ == '__main__':
    app.run(debug=True)
