#!/usr/bin/python

import os
import signal
import sys
from socket import *

kDataDir = "./logdata"
kDataExt = ".data"
kDataNum = 0
sock = None

class LogFile():
    file_dict = dict()

    def __init__(self, name):
        self.fd = open("%s/%s%s" % (kDataDir+str(kDataNum), name, kDataExt), "w")
        self.log_count = 0
        self.name = name

    def finish(self):
        if self.fd is not None:
            self.fd.close()
            self.fd = None
            print "%s logged %d messages" % (self.name, self.log_count)

    def log(self, data):
        if self.fd is not None:
            self.fd.write("%s\n" % (data, ))
            self.fd.flush()
            self.log_count = self.log_count + 1

    @staticmethod
    def finish_all():
        for v in LogFile.file_dict.values():
            v.finish()

    @staticmethod
    def get(name):
        if name not in LogFile.file_dict:
            LogFile.file_dict[name] = LogFile(name)
        return LogFile.file_dict[name]

def ctrlc_handler(signum, frame):
    # do cleanup here
    if sock != None:
        sock.close()

    LogFile.finish_all()

    print 'Finished'

    sys.exit(0)

def main():
    global kDataNum
    while os.path.exists(kDataDir+str(kDataNum)):
        kDataNum = kDataNum+1
    os.makedirs(kDataDir+str(kDataNum))

    sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    sock.bind( ('', 5454) )

    signal.signal(signal.SIGINT, ctrlc_handler)
    signal.signal(signal.SIGTERM, ctrlc_handler)

    print 'Capturing...'

    while True:
        line = sock.recv(1024)
        data = dict([ x.split('=',1) for x in line.split(',',3) ])
        if 'file' in data:
            print "Logging from",data['file']
            f = LogFile.get(data['file'])
            f.log(line)

if __name__ == "__main__":
    main()
