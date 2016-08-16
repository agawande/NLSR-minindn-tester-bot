""" Test NLSR with Mini-NDN and post comments on Gerrit """

import time
import subprocess
import os

from requests.auth import HTTPDigestAuth
from pygerrit.rest import GerritRestAPI

class TestNLSR():
    def __init__():
        self.work_dir = "/tmp"
        self.ndncxx_dir = "ndn-cxx"
        self.nfd_dir = "NFD"
        self.nlsr_dir = "NLSR"
        self.url = "https://gerrit.named-data.net"
        self.auth = HTTPDigestAuth('ashlesh', 'iJU2hMD1r61M')
        self.rest = GerritRestAPI(url=self.url, auth=self.auth)
        self.changes = []
        self.tested = {}

    def updateSrc(source):
        """ Update dependency helper """
        os.chdir(source)
        subprocess.call("git pull".split())
        subprocess.call("./waf distclean".split())
        if source != self.nlsr_dir:
            if source == self.nfd_dir:
                subprocess.call("./waf configure --without-websocket".split(), stderr=subprocess.STDOUT)
            else:
                subprocess.call("./waf configure".split(), stderr=subprocess.STDOUT)
            subprocess.call("./waf", stderr=subprocess.STDOUT)
            subprocess.call("sudo ./waf install".split(), stderr=subprocess.STDOUT)
        else:
            return 0

    def updateDep():
        """ Update dependencies """
        directory = [self.ndncxx_dir, self.nfd_dir, self.nlsr_dir]
        for source in directory:
            print source
            full_source = "{}/{}".format(self.work_dir, source)
            print full_source
            # dir does not exist and build folder does not exists
            if not os.path.isdir(full_source) and not os.path.isdir(full_source.format("build")):
                clone = "git clone --depth 1 https://github.com/named-data/{} {}" \
                        .format(source, full_source)
                subprocess.call(clone.split())
            updateSrc(full_source)

     def getChangesToTest():
         # Get open NLSR changes already verified by Jenkins and mergable
         self.changes = REST.get("changes/?q=status:open+project:NLSR+ \
                             reviewedby:jenkins+is:mergeable+label:verified")

     def fetchChanges():
         

while 1:
    tested = {}

    getChangesToTest()

    # iterate over testable changes
    for change in changes:
        print "Checking patch: {}".format(change['subject'])
        change_id = change['change_id']
        print change_id
        change_num = change['_number']
        currentRev = REST.get("/changes/?q=%s&o=CURRENT_REVISION" % change_num)
        tmp = currentRev[0]['revisions']
        for x in tmp:
            patch = tmp[x]['_number']
            ref = tmp[x]['ref']
        print patch
        print ref
        if change_id in tested:
            # check if the change has been merged/abandoned, if so remove from tested
            if REST.get("changes/?q=status:open+%s" % change_num) is None:
                tested.pop(change_id, None)
            continue
        else:
            # update source
            if updateDep() != 0:
                print "Unable to compile!"
            print "Testing patch ..."
            patch_download_cmd = "git fetch {} refs/changes/{}/{}/{}" \
                                 .format(URL, ref, change_id, patch)
            subprocess.call(patch_download_cmd)
            subprocess.call("git checkout FETCH_HEAD")
            # Check if there has been a change in cpp, hpp, or wscript files
            #if subprocess.call("git status | grep \"\cpp\|hpp\|wscript\|waf"") != 0:
                # Test the change
            #    testNLSR()
            #else:
            #    comment("No changes found in cpp,hpp,wscript, or waf files")
            # git checkout the patch
            # git status grep cpp, hpp, wscript
            # (in cpp, hpp files check if only comments have been changed)
            # Add change to tested
            tested[change_id] = ref

    time.sleep(5)
    #break
