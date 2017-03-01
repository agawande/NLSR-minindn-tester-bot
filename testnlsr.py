""" Test NLSR with Mini-NDN and post comments on Gerrit """

import time
import subprocess
import os
import sys
import argparse
import json
import shutil

from pygerrit2.rest import GerritRestAPI
from pygerrit2.rest import GerritReview
from pygerrit2.rest.auth import HTTPDigestAuthFromNetrc

class TestNLSR(object):
    """ Test NLSR class """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, options):
        self.nlsr_exp_file = os.path.abspath(options.nlsr_exp_file)
        self.work_dir = os.path.abspath(options.work_dir)
        self.exp_names = ""
        self.ndncxx_dir = "{}/ndn-cxx".format(self.work_dir)
        self.nfd_dir = "{}/NFD".format(self.work_dir)
        self.nlsr_dir = "{}/NLSR".format(self.work_dir)
        self.minindn_dir = "{}/mini-ndn".format(self.work_dir)
        self.url = "https://gerrit.named-data.net"
        self.auth = HTTPDigestAuthFromNetrc(url=self.url)
        self.rest = GerritRestAPI(url=self.url, auth=self.auth)
        self.rev = GerritReview()
        self.message = ""
        self.score = 0
        self.labels = {}
        # Need to check whether these directories exist first
        #subprocess.call("rm -rf {}/build".format(self.ndncxx_dir).split())
        #subprocess.call("rm -rf {}/build".format(self.nfd_dir).split())
        #subprocess.call("rm -rf {}/build".format(self.nlsr_dir).split())
        #REMOVE # FROM ABOVE LINES
        self.clearTmp()

    def clearTmp(self):
        os.chdir("/tmp")
        dir = [d for d in os.listdir('/tmp') if os.path.isdir(os.path.join('/tmp', d))]
        for f in dir:
            if not f.startswith('.'):
                shutil.rmtree(f)

    def update_src(self, source):
        """ Update dependency helper """
        os.chdir(source)
        subprocess.call("git checkout master".split())
        update_needed = subprocess.check_output("git pull".split())
        print(source)
        # Is upto date and build folder exists
        if update_needed.strip() == "Already up-to-date." and \
           os.path.isdir("{}/build".format(source)):
            print "{} already up to date".format(source)
            return 0

        if source == self.minindn_dir:
            os.chdir(self.minindn_dir)
            ret = subprocess.call("sudo ./install.sh -i".split())
            return ret

        subprocess.call("./waf distclean".split())
        if self.nlsr_dir != source:
            if self.nfd_dir == source:
                ret = subprocess.call("./waf configure --without-websocket".split())
            else:
                ret = subprocess.call("./waf configure".split())
            if subprocess.call("./waf -j2".split()) != 0:
                return ret
            subprocess.call("sudo ./waf install".split())
            # Need to update NFD after ndn-cxx is updated so clean the build folder of NFD!
            # So that next time this method is called NFD is guaranteed to be recompiled
            if source == self.ndncxx_dir:
                os.chdir(self.nfd_dir)
                subprocess.call("./waf distclean".split())
        return 0

    def update_dep(self):
        """ Update dependencies """
        directory = [self.ndncxx_dir, self.nfd_dir, self.nlsr_dir, self.minindn_dir]
        for source in directory:
            print source
            dir_name = source.split("/")[len(source.split("/"))-1]
            if not os.path.isdir(source):
                clone = "git clone --depth 1 https://github.com/named-data/{} {}" \
                        .format(dir_name, source)
                subprocess.call(clone.split())
            ret = self.update_src(source)
            if ret != 0:
                return ret
        return 0

    def clean_up(self, change_id, dir):
        """ Clean up git"""
        os.chdir(dir)
        print "Cleaning NLSR/Mini-NDN git branch"
        subprocess.call("git checkout master".split())
        print subprocess.check_output("git branch -v".split())
        subprocess.call("git branch -D {}".format(change_id).split())

    def has_code_changes(self):
        """ Check if the patch has code changes """
        os.chdir(self.nlsr_dir)
        out = subprocess.check_output("git diff --name-status HEAD~1".split())
        if "cpp" in out or "hpp" in out or "wscript" in out or "nlsr.conf" in out:
            return True
        return False

    def run_tests(self):
        """ Convergence test """
        subprocess.call("sudo ldconfig".split())
        self.exp_names = ""
        with open(self.nlsr_exp_file) as test_file:
            for line in test_file:
                exp = line.split(":")
                test_name = exp[0]
                print "Running minindn test {}".format(test_name)
                print test_name
                self.exp_names += test_name + "\n\n"
                proc = subprocess.Popen(exp[1].split())
                proc.wait()
                self.clearTmp()
                subprocess.call("mn --clean".split())
                if proc.returncode == 1:
                    return 1, test_name
        return 0, test_name

    def test_nlsr(self):
        """ Update and run NLSR test """
        os.chdir(self.nlsr_dir)
        self.message = ""
        subprocess.call("./waf distclean".split())
        subprocess.call("./waf configure".split())
        subprocess.call("./waf -j2".split())
        subprocess.call("sudo ./waf install".split())
        code, test = self.run_tests()
        if code == 1:
            print "Test {} failed!".format(test)
            self.message = "NLSR tester bot: Test {} failed!".format(test)
            self.score = -1
            return 1
        else:
            print "All tests passed!"
            self.message = "NLSR tester bot: \n\nAll tests passed! \n\n"
            self.message += self.exp_names
            print self.message
            self.score = 1
        return 0

    def test_minindn(self):
        """ Update and run Mini-NDN test"""
        os.chdir(self.minindn_dir)
        self.message = ""
        subprocess.call("sudo ./install.sh -i".split())

        exp = subprocess.check_output("minindn --list-experiments".split())
        exp = exp.replace("  ", "")
        exp = exp.split("\n")
        exp = exp[1:len(exp)-1]

        code = 0
        self.exp_names = ""
        for test_name in exp:
            if test_name == "failure":
                continue
            print "Running minindn test {}".format(test_name)
            print test_name
            self.exp_names += test_name + "\n\n"
            exp_full = "sudo minindn --experiment {} --no-cli --ctime 90".format(test_name)
            proc = subprocess.Popen(exp_full.split())
            proc.wait()
            self.clearTmp()
            subprocess.call("mn --clean".split())
            if proc.returncode == 1:
               code = 1
               test = test_name
               break

        if code == 1:
            print "Test {} failed!".format(test)
            self.message = "Mini-NDN tester bot: Test {} failed!".format(test)
            self.score = -1
            return 1
        else:
            print "All tests passed!"
            self.message = "Mini-NDN tester bot: \n\nAll tests passed! \n\n"
            self.message += self.exp_names
            print self.message
            self.score = 1
        return 0


    def get_changes_to_test(self):
        """ Pull the changes testable patches """
        # Get open NLSR changes already verified by Jenkins and mergable and not verified by self
        changes = self.rest.get("changes/?q=status:open+project:NLSR+branch:master+is:mergeable+label:verified+label:Verified-Integration=0")

        testMinindn = False

        if len(changes) == 0:
            changes = self.rest.get("changes/?q=status:open+project:mini-ndn+is:mergeable+label:Verified=0")
            testMinindn = True

        print("changes", changes)

        # iterate over testable changes
        for change in changes:
            print "Checking patch: {}".format(change['subject'])
            change_id = change['change_id']
            print change_id
            change_num = change['_number']

            current_rev = self.rest.get("/changes/?q={}&o=CURRENT_REVISION".format(change_num))
            #print current_rev
            tmp = current_rev[0]['revisions']
            for item in tmp:
                patch = tmp[item]['_number']
                ref = tmp[item]['ref']
            print patch
            print ref

            # update source
            if self.update_dep() != 0:
                print "Unable to compile!"
                self.rev.set_message("NLSR tester bot: Unable to compile this patch!")
                self.rev.add_labels({'Verified': 0})
            elif testMinindn == False:
                print "Pulling NLSR patch to a new branch..."
                os.chdir(self.nlsr_dir)
                subprocess.call("git checkout -b {}".format(change_id).split())
                patch_download_cmd = "git pull {}/NLSR {}".format(self.url, ref)
                print patch_download_cmd
                subprocess.call(patch_download_cmd.split())

                # Check if there has been a change in cpp, hpp, or wscript files
                if self.has_code_changes():
                    # Test the change
                    print "Testing NLSR patch"
                    self.test_nlsr()
                    print "Commenting"
                    self.rev.set_message(self.message)
                    self.rev.add_labels({'Verified-Integration': self.score})
                else:
                    print "No change in code"
                    self.rev.set_message("NLSR tester bot: No change in code, skipped testing!")
                    self.rev.add_labels({'Verified-Integration': 1})
                self.clean_up(change_id, self.nlsr_dir)
            else:
                print "Pulling Mini-NDN patch to a new branch..."
                os.chdir(self.minindn_dir)
                subprocess.call("git checkout -b {}".format(change_id).split())
                patch_download_cmd = "git pull {}/mini-ndn {}".format(self.url, ref)
                print patch_download_cmd
                subprocess.call(patch_download_cmd.split())

                # Test the change
                print "Testing Mini-NDN patch"
                self.test_minindn()
                print "Commenting"
                self.rev.set_message(self.message)
                self.rev.add_labels({'Verified': self.score})

                self.clean_up(change_id, self.minindn_dir)

            print self.rev
            self.rest.review(change_id, patch, self.rev)

            print "\n--------------------------------------------------------\n"
            time.sleep(60)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Mini-NDN NLSR tester for gerrit')

    parser.add_argument('nlsr_exp_file', help='specify NLSR experiment file')

    parser.add_argument('work_dir', help='specify working dir other than /tmp')

    args = parser.parse_args()
    print args.nlsr_exp_file
    print args.work_dir

    TEST = TestNLSR(args)

    while 1:
        TEST.get_changes_to_test()
        time.sleep(900)
