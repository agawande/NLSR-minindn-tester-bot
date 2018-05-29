from pygerrit2.rest.auth import HTTPBasicAuthFromNetrc, HTTPDigestAuthFromNetrc
from pygerrit2.rest import GerritRestAPI
from pygerrit2.rest import GerritReview

review = GerritReview()
review.set_message("testing2")
review.add_labels({'Verified-Integration': 0})

url = "https://gerrit.named-data.net"
auth = HTTPBasicAuthFromNetrc(url)
rest = GerritRestAPI(url, auth=auth)

print(review)

print(rest.review("4763", 2, review))