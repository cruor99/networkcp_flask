__author__ = 'cruor'
import subprocess
import os


class Server(object):

    def serverstart(self, user):
        print user
        os.chdir("/home/cruor/"+user)#endres ved production
        self.process = subprocess.Popen(["./minecraft.sh", "start"], close_fds=True, stdout=subprocess.PIPE)
        output = self.process.stdout.read()

    def serverread(self, user):
        os.chdir("/home/cruor/"+user)#endres ved production
        self.process = subprocess.Popen("./read.sh", close_fds=True, stdout=subprocess.PIPE)
        return self.process.stdout.read()
