#!/usr/bin/env python
import feedparser, sys, time, calendar, uploader

def parse_rss(rss_url, last_run):
# parse the global rss feed for the filter, creating a list of docs to create/update
	# create a new parser from RSS feed
	fp = feedparser.parse(rss_url)
	# create list of cases needing update 
	updates = []
	for entry in fp.entries:
		timestamp = unixTime(entry.published)

		# if more recent than last run, this entry has an update
		if timeStamp > last_run:
			case = entry.title.split(':')[0].lstrip('Case ')
			updates.append(case)
	return updates


# convert fogbugz rss date into Unix timestamp
def unixTime(timestamp):
>>>>>>> 20337-uploader
	return calendar.timegm(time.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z"))


if __name__=='__main__':
	rss_URL = sys.argv[1]
	last_run = int(sys.argv[2])
	updates = ["1"]
	#  updates = parseRSS(rssURL, lastRun)
	success = []
	for case in updates:
		# create the json
		# call to docBuilder function here
  		u = uploader.upload(json_doc)
  		if u:
  			success.append(u)
  	# success if lengths match (as many successes as docs)
  	print len(success) == len(updates)
  	### update last_run (or I suppose Cron handles this) ###