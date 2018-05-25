from os import listdir
import time

class LogManager():

    def __init__(self, changeNum, logDirectory):
        self.logFile = open("{}/{}-logs.txt".format(logDirectory, changeNum), "a")

    def writeLogs(self, experiment_name):
        self.logFile.write(experiment_name + "\n\r")
        nodeList = listdir("/tmp/minindn/")
        print(nodeList)
        for node in nodeList:
            self.logFile.write(node + "\n\r***********************\n\r")
            time.sleep(1)
            nodeLog = open("/tmp/minindn/{}/log/nlsr.log".format(node), "r")
            self.logFile.write(nodeLog.read())
            time.sleep(1)
        self.logFile.write("\n\r***********************\n\r")