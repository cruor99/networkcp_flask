from flask import *
from flask import request
import deployserv
import socket
app = Flask(__name__)
serverstart = 'START'

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():



@app.route('/server', methods=['GET', 'POST'])
def servermonitor():
    error=None
    #checks to initiate server script method
    #NOT COMPLETE, ONLY TEST FOR NOW
    serv = deployserv.Server()

    if request.method=='GET':
        serv.serverStart()
        return render_template('server.html')

    if request.method=='POST':
        serv.serverStart()
        return render_template('server.html')
    else:
        error='Did not INIT'
    return render_template('server.html')

if __name__ == '__main__':
    app.run(debug=True)
