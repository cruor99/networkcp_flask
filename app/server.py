__author__ = 'cruor'
import subprocess
import paramiko
import threading
import os

basedir = os.path.abspath(os.path.dirname(__file__))
upload_dir = os.path.join(basedir, 'tmp')


#Handles everything to do with remote server access, such as deploying servers to remote locations,
#as well as starting, stopping and communicating with these servers.as
class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    #starts the server using subprocess.Popen, and using the minecraft.sh script with the 'start' argument
    def serverstart(self, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('84.49.16.80', username='minecraft', password='minecraft')
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("dtach -n "+user+" /etc/init.d/minecraft_server start "+user)
        print ssh_stdout.readlines()
        #ssh_stdout.flush()
    #Stops the server using subprocess.Popen, using the minecraft.sh script with the 'stop' argument
    def serverstop(self, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('84.49.16.80', username='minecraft', password='minecraft')
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("dtach -n "+user+"st /etc/init.d/minecraft_server stop "+user)
        print ssh_stdout.readlines()
    def servercreate(self, server, user, port):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('84.49.16.'+server, username='minecraft', password='minecraft')
        ssh.exec_command("dtach -n "+user+"cr /etc/init.d/minecraft_server create "+user+" "+port)
    #Method for reading information from the server, currently not working and a redesign is planned
    def serverstatus(self, user):
        self.process = subprocess.Popen(["/etc/init.d/minecraft_server", "list", "running"], close_fds=True, stdout=subprocess.PIPE)
        return self.process.stdout.read()

    def readconsole(self, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('84.49.16.80', username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("tail --lines 15 /home/minecraft/worlds/"+user+"/console.out")
        return ssh_stdin.readlines()

    #Method for sending commands to server
    def servercommand(self, user, command):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('84.49.16.80', username='minecraft', password='minecraft')
        ssh.exec_command("dtach -n "+user+"cr /etc/init.d/minecraft_server send "+user+" "+command)

    #Method to get the server.properties file
    def readproperties(self, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('84.49.16.80', username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("tail --lines=35 /home/minecraft/worlds/"+user+"/server.properties")
        return ssh_stdin.readlines()

    #Method for sending files
    def sendfile(self,server,filename,user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('84.49.16.'+server, username='minecraft', password='minecraft')
        sftp = ssh.open_sftp()
        localpath = upload_dir+'/' + filename
        remotepath = '/home/minecraft/worlds/'+user+'/'+filename
        sftp.put(localpath, remotepath)
        sftp.close()
        ssh.close()

    def unzip(self, user, filename):
        homedir = "/home/minecraft/worlds/"+user+"/"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('84.49.16.80', username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("unzip "+homedir+filename+" -d "+homedir)
        return ssh_stdin.readlines()

    #Method for editing server.properties
    def editproperties(self, user, key, value):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('84.49.16.80', username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("python /home/minecraft/mcprop.py -w "+user+" -o "+key+" -v "+value)
        return ssh_stdin.readlines()

    def deleteserv(self, user):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('84.49.16.80', username='minecraft', password='minecraft')
        ssh_stdout, ssh_stdin, ssh_stderr = ssh.exec_command("rm -rf /home/minecraft/worlds/"+user+"/*")
        return ssh_stdin.readlines()