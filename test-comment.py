from requests.auth import HTTPDigestAuth
from pygerrit.rest import GerritRestAPI
from pygerrit.rest import GerritReview

auth = HTTPDigestAuth('ashlesh', 'iJU2hMD1r61M')
#https is required to post comments
rest = GerritRestAPI(url='https://gerrit.named-data.net', auth=auth)

currentRev = rest.get("changes/?q=3061&o=CURRENT_REVISION")
tmp = currentRev[0]['revisions']

change_id = "Ia04f0895de9906e280d6140f775bb6609db714e6"
#print tmp

for x in tmp:
    reviewid = x
    patch = tmp[x]['_number']
    ref = tmp[x]['ref']
    print patch
    print ref

#change_id = "Ia04f0895de9906e280d6140f775bb6609db714e6"

#print(change_id)
#print(reviewid)
rev = GerritReview("", labels={'Code-Review': '+1'})
#print rev
rvd = rest.review("1941", "4", rev)
print rvd == None

#for tcm in rvd:
#    print tcm
