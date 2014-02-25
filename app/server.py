__author__ = 'cruor'
import subprocess
import paramiko
import os



#Handles everything to do with remote server access, such as deploying servers to remote locations,
#as well as starting, stopping and communicating with these servers.as
class Server(object):

#starts the server using subprocess.Popen, and using the minecraft.sh script with the 'start' argument
    def serverstart(self, user):
        ssh = paramiko.SSHCliet()
        ssh.connect('84.49.16.80', username='steve', password='12Karen34')
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("/etc/init.d/minecraft_server start server5")

#Stops the server using subprocess.Popen, using the minecraft.sh script with the 'stop' argument
    def serverstop(self, user):
        self.process = subprocess.Popen(["/etc/init.d/minecraft_server", "stop "+user], close_fds=True)

    def servercreate(self, user):
        self.process = subprocess.Popen(["/etc/init.d/minecraft_server", "create "+user], close_fds=True)
#Method for reading information from the server, currently not working and a redesign is planned
    def serverread(self, user):
        self.process = subprocess.Popen(["/etc/init.d/minecraft_server", "list", "enabled"], close_fds=True, stdout=subprocess.PIPE)
        return self.process.stdout.read()
