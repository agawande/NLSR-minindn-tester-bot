""" Test NLSR with Mini-NDN and post comments on Gerrit """

import time
import subprocess
import os
import sys

from requests.auth import HTTPDigestAuth
from pygerrit.rest import GerritRestAPI
from pygerrit.rest import GerritReview

class TestNLSR(object):
    """ Test NLSR class"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, exp_file):
        self.exp_file = os.path.abspath(exp_file)
        self.work_dir = "/tmp"
        self.ndncxx_dir = "ndn-cxx"
        self.nfd_dir = "NFD"
        self.nlsr_dir = "NLSR"
        self.url = "https://gerrit.named-data.net"
        self.auth = HTTPDigestAuth('ashlesh', '')
        self.rest = GerritRestAPI(url=self.url, auth=self.auth)
        self.rev = GerritReview()
        self.tested = {}
        self.message = ""
        self.score = 0
        self.labels = {}

    def update_src(self, source):
        """ Update dependency helper """
        os.chdir(source)
        update_needed = subprocess.check_output("git pull".split())
        if update_needed.strip() == "Already up-to-date.":
            print "{} already up to date".format(source)
            return 0
        subprocess.call("./waf distclean".split())
        if self.nlsr_dir not in source:
            if self.nfd_dir in source:
                ret = subprocess.call("./waf configure --without-websocket".split(), \
                                stderr=subprocess.STDOUT)
            else:
                subprocess.call("./waf configure".split(), stderr=subprocess.STDOUT)
            if ret != 0:
                return ret
            return subprocess.call("sudo ./waf install".split(), stderr=subprocess.STDOUT)
        return 0

    def update_dep(self):
        """ Update dependencies """
        directory = [self.ndncxx_dir, self.nfd_dir, self.nlsr_dir]
        for source in directory:
            print source
            full_source = "{}/{}".format(self.work_dir, source)
            print full_source
            # dir does not exist and build folder does not exists
            if not os.path.isdir(full_source): #and not os.path.isdir(full_source.format("build")):
                clone = "git clone --depth 1 https://github.com/named-data/{} {}" \
                        .format(source, full_source)
                subprocess.call(clone.split())
            ret = self.update_src(full_source)
            if ret != 0:
                return ret
        return 0

    def clean_up(self, change_id):
        """ Clean up git NLSR"""
        subprocess.call("git checkout master".split())
        subprocess.call("git branch -D {}".format(change_id).split())

    def has_code_changes(self):
        """ Check if the patch has code changes """
        os.chdir("/tmp/NLSR")
        out = subprocess.check_output("git diff --name-status HEAD~1".split())
        if "cpp" in out or "hpp" in out or "wscript" in out:
            return True
        return False

    def test(self):
        """ Convergence test """
        with open(self.exp_file) as test_file:
            i = 1
            for line in test_file:
                print "Running minindn test {}".format(i)
                proc = subprocess.Popen(line.split())
                proc.wait()
                if proc.returncode == 1:
                    return 1, i
                i += 1
        return 0, i

    def test_NLSR(self):
        """ Update and run test """
        os.chdir("{}/{}".format(self.work_dir, self.nlsr_dir))
        subprocess.call("./waf distclean".split())
        subprocess.call("./waf configure".split())
        subprocess.call("./waf")
        subprocess.call("sudo ./waf install".split())
        code, test = self.test()
        if code == 1:
            print "Test {} failed!".format(test)
            self.message = "Test {} failed!".format(test)
            self.score = -1
            return 1
        else:
            print "All tests passed!"
            self.message += "All tests passed!"
            self.score = 1

    def get_changes_to_test(self):
        """ Pull the changes testable patches """
        # Get open NLSR changes already verified by Jenkins and mergable
        changes = self.rest.get("changes/?q=status:open+project:NLSR+ \
                                reviewedby:jenkins+is:mergeable+label:verified")

        # iterate over testable changes
        for change in changes:
            print "Checking patch: {}".format(change['subject'])
            change_id = change['change_id']
            print change_id
            change_num = change['_number']

            current_rev = self.rest.get("/changes/?q=%s&o=CURRENT_REVISION" % change_num)
            tmp = current_rev[0]['revisions']
            for item in tmp:
                patch = tmp[item]['_number']
                ref = tmp[item]['ref']
            print patch
            print ref
            if change_id in self.tested:
                print "Already tested!"
                #USE A FILE INSTEAD OF SELF.TESTED SO THAT WE CAN RECOVER FROM FATAL FAILURES
                # check if the change has been merged/abandoned, if so remove from tested
                if self.rest.get("changes/?q=status:open+%s" % change_num) is None:
                    self.tested.pop(change_id, None)
                    continue
            else:
                # update source
                if self.update_dep() != 0:
                    print "Unable to compile!"
                    self.clean_up(change_id)
                else:
                    print "Pulling patch to a new branch..."
                    subprocess.call("git checkout -b {}".format(change_id).split())
                    patch_download_cmd = "git pull {}/NLSR {}".format(self.url, ref)
                    print patch_download_cmd
                    subprocess.call(patch_download_cmd.split())

                    # Check if there has been a change in cpp, hpp, or wscript files
                    if self.has_code_changes():
                        # Test the change
                        print "Testing NLSR patch"
                        self.test_NLSR()
                        print "Commenting"
                        self.rev.set_message(self.message)
                        self.rev.add_labels({'Verified': self.score})
                        print self.rev
                        #self.rest.review(change_id, patch, self.rev)
                    else:
                        print "No change in code"
                    # clean the NLSR directory
                    self.clean_up(change_id)
                self.tested[change_id] = ref
            print "\n--------------------------------------------------------\n"

if __name__ == "__main__":
    TEST = TestNLSR(sys.argv[1])

    while 1:
        TEST.get_changes_to_test()
        time.sleep(60)
