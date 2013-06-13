#!/usr/bin/env python
import feedparser, sys, time, calendar

def parseRSS(rssURL, lastRun):
	# create a new parser from RSS feed
	fp = feedparser.parse(rssURL)
	# create list of cases needing update 
	updates = []
	for entry in fp.entries:
		timeStamp = unixTime(entry.published)

		# if more recent than last run, this entry is an update
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

  updates = parseRSS(rssURL, lastRun)
  for case in updates:
  	# create the json
  	# upload the doc to Cloudant