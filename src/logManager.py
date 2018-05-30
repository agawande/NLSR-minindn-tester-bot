from os import listdir
from os.path import isfile
import time

class LogManager():

    def __init__(self, changeNum, logDirectory):
        self.logFile = open("{}/{}-logs.txt".format(logDirectory, changeNum), "a")

    def writeLogs(self, experiment_name):
        self.logFile.write("!!{}!!".format(experiment_name) + "\n\r")
        nodeList = listdir("/tmp/minindn/")
        for node in nodeList:
            self.logFile.write("\n\r{} Log - NLSR".format(node) + "\n\r***********************\n\r")
            #time.sleep(1)
            nlsrLogPath = "/tmp/minindn/{}/log/nlsr.log".format(node)
            if isfile(nlsrLogPath):
                nodeNlsrLog = open(nlsrLogPath, "r")
                self.logFile.write(nodeNlsrLog.read())
            #time.sleep(1)
            self.logFile.write("\n\r{} Log - NFD".format(node) + "\n\r***********************\n\r")
            nfdLogPath = "/tmp/minindn/{}/nfd.log".format(node)
            if isfile(nlsrLogPath):
                    nodeNfdLog = open(nfdLogPath, "r")
                    self.logFile.write(nodeNfdLog.read())
            self.logFile.write("***********************\n\r")