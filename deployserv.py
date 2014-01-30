__author__ = 'cruor'

import subprocess
import os
import socket
import threading
from time import sleep


cHost = 'localhost'
cPort = 25566
cBuffer = 0
cClients = 10
cPassword = "test"
startScriptPath = "/home/cruor/mcServer/start.sh"
scriptpathenc = startScriptPath.encode()
class Server(object):
    def __init__(self):
        self.process = False
        folder = "/home/cruor/mcServer"
    def serverStart(self, user):
        os.chdir("/home/cruor/"+user)
        self.process =subprocess.Popen("./start.sh", close_fds=True)

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

serv = Server()

def client(cnct, adr):
    global count
    try:
        dat = str(cnct.recv(cBuffer)).split(" ")
        ans = False
        if dat[0] == "start":
            print "Client %s:%s started the MC Server....."%(adr[0], adr[1])
            x = serv.serverStart()
            sleep(1)
            serv.serverCom(" ")
            serv.serverCom(" ")
            sleep(5)
            if x:
                ans = "Server is now online."
            else:
                ans = "Server is already online."
        elif dat[0] == "stop":
            print "Client %s:%s stopped the MC Server....."%(adr[0], adr[1])
            x = serv.serverStop()
            sleep(6)
            if x:
                ans = "Server is now offline."
            else:
                ans = "Server is already offline."
        elif dat[0] == "commun":
            print "Client %s:%s executed a command on the MC Server....."%(adr[0], adr[1])
            serv.serverCom(" ".join(dat[1:]))
            x = serv.serverCom(" ")
            if x[1]:
                ans = x[0]
            else:
                ans = "No return text, server is offline or not responding."
        elif dat[0] == "players":
            print "Client %s:%s recieved the player count from the MC Server....."%(adr[0], adr[1])
            pc = serv.serverPlayers()
            ans = "%s/%s"%(pc[0],pc[1])
        elif dat[0] == "help":
            print "Client %s:%s recieved the help list....."%(adr[0], adr[1])
            ans = "__________\nstart - Starts the server.\nstop - Stops the server.\ncommun <command> - Writes to server's console.\nplayers - Returns player count.\nhelp - Shows this help.\nclose - Closes client connections.\n__________"
        elif dat[0] == "close":
            pass
        else:
            ans = "Command '%s' is not valid."%dat[0]
        if ans:
            cnct.send("PASS")
            cnct.send("%s\n"%ans)
            threading.Thread(target = client, args = (cnct, adr,)).start()
        else:
            cnct.send("DICN")
            cnct.send("Connection to server closed.\n")
            cnct.close()
            print "Client %s:%s disconnected....."%(adr[0], adr[1])
            if count:
                count -= 1
    except:
        cnct.close()
        print "Client %s:%s disconnected..... "%(adr[0], adr[1])
        if count:
            count -= 1


def servsock():
    print "-MC Server Control v0.0.1 Alpha"
    print "Attempting server start..."
    print "Connecting to socket..."
    serv.serverStart()
    sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sck.bind((cHost, cPort))
    sck.listen(5)
    print "Connected and listening on %s:%s....."%(cHost, cPort)
    while True:
        for x in range(cClients):
            (cnct, adr) = sck.accept()
            print "Client %s:%s connected....."%(adr[0], adr[1])
            serv.serverStart()
#def servsock():
#    print "-MC Server Control Server v0.0.1 BETA-"
#    print "Starting up server....."
#    print "Connecting to socket....."
#    count = 0
#    serv.serverStart()
#    sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    sck.bind((cHost, cPort))
#    sck.listen(5)
#    print "Connected and listening on %s:%s....."%(cHost, cPort)
#    print "Setting up client listener, allowing %s clients to connect at a time....."%cClients
#    serv.serverCom("go die!")
#    while True:
#        for x in range(cClients):
#            serv.serverCom("go die!")
#            (cnct, adr) = sck.accept()
#            print "Client %s:%s connected....."%(adr[0], adr[1])
#            cnct.send("Welcome to MineCraft Server Control.\n\nPlease enter server control password.\n")
#            ps = str(cnct.recv(cBuffer))
#            if count < cClients:
#                if ps == cPassword:
#                    cnct.send("CRRT")
#                    cnct.send("%s was correct.\nIf you need help type 'help'."%ps)
#                    count += 1
#                    threading.Thread(target = client, args = (cnct, adr,)).start()
#                else:
#                    cnct.send("WRNG")
#                    cnct.send("%s wasn't the correct password, please try again."%ps)
#                    cnct.close()
#                    print "Client %s:%s rejected....."%(adr[0], adr[1])
#            else:
#                cnct.send("WRNG")
#                cnct.send("Too many clients connected to MineCraft Server Control")
#                cnct.close()
#                print "Client %s:%s rejected....."%(adr[0], adr[1])
#
#    sck.close()