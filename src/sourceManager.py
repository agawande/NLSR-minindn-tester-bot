import os
from subprocess import call, check_output

class SourceManager(object):
    """ Source Update Manager class """

    def __init__(self, repoDir):

    	self.repoDir = repoDir

        self.repoName = repoDir.split("/")[len(repoDir.split("/"))-1]
        print(self.repoName)
        
        if self.repoName != "ndn-cxx":
            NDN_GIT = "https://gerrit.named-data.net"
        else:
            NDN_GIT = "https://github.com/named-data"

        if not os.path.isdir(repoDir):
            call("git clone --depth 1 {}/{} {}".format(NDN_GIT, self.repoName, self.repoDir).split())

        if self.repoName == "NFD":
            self.configCmd = "./waf configure --without-websocket"
        else:
            self.configCmd = "./waf configure"
        self.compileCmd = "./waf -j2"
        self.installCmd = "./waf install"

    def scall(self, cmd):
        return call(cmd.split(), cwd = self.repoDir)

    def scheck(self, cmd):
        return check_output(cmd.split(), cwd = self.repoDir)

    def update_and_install(self):
        # If build is already there then it means it has been compiled before
        if "Already up-to-date." in self.scheck("git pull origin master") and \
           "build" in self.scheck("ls"):
            return 0
        return self.install()

    def install(self):
        if self.repoName != "mini-ndn":
            return self.scall("./waf distclean") or \
                   self.scall(self.configCmd) or \
                   self.scall(self.compileCmd) or \
                   self.scall(self.installCmd) or \
                   self.scall("ldconfig")
        else:
            return self.scall("./install.sh -i")

    def checkout_new_branch(self, branchName):
        # If checkout fails due to branch already existing
        # which is due to ungraceful exit of the test program before
        if self.scall("git checkout -b {}".format(branchName)) != 0:
            self.scall("git checkout master")
            self.delete_branch(branchName)
            self.scall("git checkout -b {}".format(branchName))

    def delete_branch(self, branchName):
        self.scall("git branch -D {}".format(branchName))

    def pull_from_gerrit(self, projectUrl, refs):
        self.scall("git pull {} {}".format(projectUrl, refs))

    def clean_up(self, branchName):
        """ Clean up git"""
        print("Cleaning {} git branch".format(self.repoName))
        self.scall("git checkout master")
        self.delete_branch(branchName)

    def has_code_changes(self):
        files = self.scheck("git diff --name-only HEAD~1")
        if "cpp" in files or "hpp" in files or "wscript" in files or "nlsr.conf" in files:
            return True
        return False

    def install_target_change(self, targetURL, changeId, ref):
        return self.checkout_new_branch(changeId) and self.pull_from_gerrit("{}/{}".format(targetURL, self.repoName), ref) and self.install() and self.clean_up(changeId)