from flask import *
from flask import request
from functools import wraps
import deployserv
app = Flask(__name__)
app.secret_key='minecraft'


#def login_required(test):
#    @wraps(test)
#    def wrap(*args, **kwargs):
#        if 'logged_in' in session:
#            return test(*args, **kwargs)
#        else:
#            flash('You need to log in first.')
#            return redirect(url_for(login))
#    return wrap


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


@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')


@app.route('/server', methods=['GET', 'POST'])
def servermonitor():
    error=None
    #checks to initiate server script method
    #NOT COMPLETE, ONLY TEST FOR NOW
    serv = deployserv.Server()

    if request.method =='GET':
        serv.serverStart()


    if request.method =='POST':
        serv.serverStart()

    else:
        error='Did not INIT'
    return render_template('server.html')

if __name__ == '__main__':
    app.run(debug=True)
