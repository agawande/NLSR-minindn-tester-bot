""" Test NLSR with Mini-NDN and post comments on Gerrit """

import time
import subprocess
import os
import sys
import argparse
import json
import shutil
from sourceManager import SourceManager

from pygerrit2.rest import GerritRestAPI
from pygerrit2.rest import GerritReview
from pygerrit2.rest.auth import HTTPBasicAuthFromNetrc

class TestNLSR(object):
    """ Test NLSR class """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, options):
        self.nlsr_exp_file = os.path.abspath(options.nlsr_exp_file)
        self.work_dir = os.path.abspath(options.work_dir)
        self.exp_names = ""

        self.ndncxx_src = SourceManager("{}/ndn-cxx".format(self.work_dir))
        self.nfd_src = SourceManager("{}/NFD".format(self.work_dir))
        self.nlsr_src = SourceManager("{}/NLSR".format(self.work_dir))
        self.minindn_src = SourceManager("{}/mini-ndn".format(self.work_dir))

        self.url = "https://gerrit.named-data.net"
        self.auth = HTTPBasicAuthFromNetrc(self.url)
        self.rest = GerritRestAPI(url=self.url, auth=self.auth)
        self.rev = GerritReview()
        self.message = ""
        self.score = 0
        self.labels = {}
        self.clear_tmp()

    def clear_tmp(self):
        os.chdir("/tmp")
        dir = [d for d in os.listdir('/tmp') if os.path.isdir(os.path.join('/tmp', d))]
        for f in dir:
            if not f.startswith('.'):
                shutil.rmtree(f)

    def run_tests(self):
        self.exp_names = ""
        with open(self.nlsr_exp_file) as test_file:
            for line in test_file:
                exp = line.split(":")
                test_name = exp[0]

                # Run two times if test fails
                i = 0
                while (i < 3):
                    print "Running minindn test {}".format(test_name)
                    print test_name
                    if i == 0:
                        self.exp_names += test_name + "\n\n"
                    proc = subprocess.Popen(exp[1].split())
                    proc.wait()
                    self.clear_tmp()
                    subprocess.call("mn --clean".split())

                    if proc.returncode != 0:
                        if i == 2:
                            return 1, test_name
                        time.sleep(30)
                    else:
                        # Test was successful
                        break
                    i += 1

                time.sleep(30)
        return 0, test_name

    def test_nlsr(self):
        """ Update and run NLSR test """
        self.message = ""
        if self.nlsr_src.install() != 0:
            self.message = "Unable to compile NLSR"
            self.score = -1
            return 1
        code, test = self.run_tests()
        if code != 0:
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

    def update_dep(self):
        """ Update dependencies """
        #gitSource = [self.ndncxx_src, self.nfd_src, self.nlsr_src, self.minindn_src]
        git_source = [self.nlsr_src, self.minindn_src]
        for source in git_source:
            if source.update_and_install() != 0:
                return 1
        return 0

    def get_and_test_changes(self):
        """ Pull the changes testable patches """
        # Get open NLSR changes already verified by Jenkins and mergable and not verified by self
        changes = self.rest.get("changes/?q=status:open+project:NLSR+branch:master+is:mergeable+label:verified+label:Verified-Integration=0")
        #changes = self.rest.get("changes/?q=4053")

        print("changes", changes)

        time.sleep(5)

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
                print "Unable to compile and install ndn-cxx, NFD, NLSR!"
                self.rev.set_message("NLSR tester bot: Unable to compile dependencies!")
                self.rev.add_labels({'Verified-Integration': 0})
            else:
                print "Pulling NLSR patch to a new branch..."
                self.nlsr_src.checkout_new_branch(change_id)
                self.nlsr_src.pull_from_gerrit("{}/NLSR".format(self.url), ref)

                # Check if there has been a change in cpp, hpp, or wscript files
                if self.nlsr_src.has_code_changes():
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
                self.nlsr_src.clean_up(change_id)

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
        TEST.get_and_test_changes()
        time.sleep(600)
