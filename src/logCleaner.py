from pygerrit2.rest import GerritRestAPI
from pygerrit2.rest.auth import HTTPBasicAuthFromNetrc
import os
import json

class LogCleaner:
    @staticmethod
    def clean_up(log_directory):
        url = "https://gerrit.named-data.net"
        auth = HTTPBasicAuthFromNetrc(url)
        rest = GerritRestAPI(url=url, auth=auth)
        logList = os.listdir(log_directory)
        for log in logList:
            if os.path.isfile("{}/{}".format(log_directory, log)) and "-logs.txt" in log:
                issue_number = log[0:4]
                issue_information = rest.get("/changes/?q={}".format(issue_number))
                try:
                    issue_status = issue_information[0]["status"]
                    if issue_status == "MERGED" or issue_status == "ABANDONED":
                        print("removing {}".format(log))
                        os.remove("{}/{}".format(log_directory, log))
                except:
                    print("Error in checking {}, passing...".format(log))
                    pass