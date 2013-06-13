#!/usr/bin/env python
import feedparser, sys, time, calendar, uploader

def parseRSS(rssURL, lastRun):
	# create a new parser from RSS feed
	fp = feedparser.parse(rssURL)
	# create list of cases needing update 
	updates = []
	for entry in fp.entries:
		timeStamp = unixTime(entry.published)

		# if more recent than last run, this entry has an update
		if timeStamp > lastRun:
			case = entry.title.split(':')[0].lstrip('Case ')
			updates.append(case)
	return updates


# convert fogbugz rss pubdate into Unix time
def unixTime(timestamp):
	return calendar.timegm(time.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z"))


if __name__=='__main__':
	rssURL = sys.argv[1]
	lastRun = int(sys.argv[2])
	updates = ["1"]
	#  updates = parseRSS(rssURL, lastRun)
	success = []
	for case in updates:
		# create the json
  		json_doc = {"_id": "2062332", "foo": "bar"}
  		u = uploader.upload(json_doc)
  		if u:
	  		""" should let us get a list of which succeeded 
	  		may be more helpful to have list of failures; 
	  		picking out values that dont appear in both lists
	  		that we can report 
	  		"""
  			success.append(u)
  	# success if lengths match
  	print len(success) == len(updates)