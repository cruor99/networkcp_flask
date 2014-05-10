__author__ = 'cruor'
import subprocess
import paramiko
import threading
import os
import time

basedir = os.path.abspath(os.path.dirname(__file__))
upload_dir = os.path.join(basedir, 'tmp')


#Handles everything to do with remote server access, such as deploying servers to remote locations,
#as well as starting, stopping and communicating with these servers.as
class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)


    #starts the server using subprocess.Popen, and using the minecraft.sh script with the 'start' argument
    def serverstart(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("dtach -n "+user+" /etc/init.d/minecraft_server start "+user)
        print ssh_stdout.readlines()
        #ssh_stdout.flush()


    #Stops the server using subprocess.Popen, using the minecraft.sh script with the 'stop' argument
    def serverstop(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("dtach -n "+user+"st /etc/init.d/minecraft_server stop "+user)
        print ssh_stdout.readlines()


    def servercreate(self, server, user, port):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("dtach -n "+user+"cr /etc/init.d/minecraft_server create "+user+" "+port)
        return ssh_stdout.readlines()


    def startvent(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='steve', password='12Karen34')
        time.sleep(3)
        ssh.exec_command("cd /home/steve/ventriloservers/"+user+"; ./ventrilo_srv-Linux -d -r/home/steve/misc/key")


    def stopvent(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='steve', password='12Karen34')
        ssh.exec_command("/home/steve/stoptest.sh /home/steve/ventriloservers/"+user+"/ventrilo_srv.pid")


    #Method for reading information from the server, currently not working and a redesign is planned
    def serverstatus(self, user):
        self.process = subprocess.Popen(["/etc/init.d/minecraft_server", "list", "running"], close_fds=True, stdout=subprocess.PIPE)
        return self.process.stdout.read()


    def readconsole(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("tail --lines 15 /home/minecraft/worlds/"+user+"/console.out")
        return ssh_stdin.readlines()


    #Method for sending commands to server
    def servercommand(self, server, user, command):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh.exec_command("dtach -n "+user+"cr /etc/init.d/minecraft_server send "+user+" "+command)


    #Method to get the server.properties file
    def readproperties(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("tail --lines=35 /home/minecraft/worlds/"+user+"/server.properties")
        return ssh_stdin.readlines()




    #Method for sending files
    def sendfile(self, server, filename, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        sftp = ssh.open_sftp()
        localpath = upload_dir+'/' + filename
        remotepath = '/home/minecraft/worlds/'+user+'/'+filename
        sftp.put(localpath, remotepath)
        sftp.close()
        ssh.close()


    def sendvent(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='steve', password='12Karen34')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("mkdir /home/steve/ventriloservers/"+user)
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("cp -r /home/steve/misc/ventpro.zip /home/steve/ventriloservers/"+user)
        return ssh_stdin.readlines()


    def deployvent(self, user, filename, server):
        homedir = "/home/steve/ventriloservers/"+user+"/"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='steve', password='12Karen34')
        ssh.exec_command("unzip "+homedir+filename+" -d "+homedir+"; chmod 777 "+homedir+"ventrilo_srv-Linux")
        time.sleep(1)
        ssh.exec_command("python /home/steve/editinit.py -w "+user+" -o intf -v "+str(server)+" -c Intf")


    def readventprops(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='steve', password='12Karen34')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("tail --lines=35 /home/steve/ventriloservers/"+user+"/ventrilo_srv.ini")
        return ssh_stdin.readlines()
        ssh.close()


    def editventprops(self, server, user, key, value):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='steve', password='12Karen34')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("python /home/steve/editinit.py -w "+user+" -o "+key+" -v "+value+" -c Server")
        return ssh_stdin.readlines()
        ssh.close()


    def unzip(self, server, user, filename):
        homedir = "/home/minecraft/worlds/"+user+"/"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("unzip "+homedir+filename+" -d "+homedir)
        return ssh_stdin.readlines()


    #Method for editing server.properties
    def editproperties(self, server, user, key, value):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("python /home/minecraft/mcprop.py -w "+user+" -o "+key+" -v "+value)
        return ssh_stdin.readlines()


    def deleteserv(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("rm -rf /home/minecraft/worlds/"+user+"/*")
        return ssh_stdin.readlines()


    def backupserv(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("/etc/init.d/minecraft_server backup "+user)
        return ssh_stdin.readlines()


    def restorebackup(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("rm -rf /home/minecraft/worlds/"+user)
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("mv /home/minecraft/backup "+user+" /home/minecraft/worlds")
        return ssh_stdin.readlines()


    def serverstatus(self, server, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("/etc/init.d/minecraft_server status "+user)
        return ssh_stdin.readlines()