from flask import *
from flask import request
import deployserv
app = Flask(__name__)
serverstart = 'START'

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
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/server', methods=['GET', 'POST'])
def servermonitor():
    error=None
    #checks to initiate server script method
    #NOT COMPLETE, ONLY TEST FOR NOW
    serv = deployserv.Server()

    if request.method=='GET':
        serv.serverStart()


    if request.method=='POST':
        serv.serverStart()

    else:
        error='Did not INIT'
    return render_template('server.html')

if __name__ == '__main__':
    app.run(debug=True)
