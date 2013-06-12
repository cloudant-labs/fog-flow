#!/usr/bin/env python
import feedparser, sys, time, calendar

def parse_rss(rss_url, last_run):
	# create a new parser from RSS feed
	fp = feedparser.parse(rssURL)
	# create list of cases needing update 
	updates = []
	for entry in fp.entries:
		timestamp = unix_time(entry.published)

		# if more recent than last run, this entry is an update
		if timestamp > last_run:
			case = entry.title.split(':')[0].lstrip('Case ')
			updates.append(case)
	return updates


# convert fogbugz rss pubdate (RFC 822) into Unix time
def unix_time(timestamp):
	return calendar.timegm(time.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z"))


if __name__=='__main__':
  
  rss_url = sys.argv[1]
  last_run = int(sys.argv[2])

  updates = parse_rss(rss_url, last_run)
  for case in updates:
  	# create the json
  	# upload the doc to Cloudant
  # update/create .ini file to reflect new lastRun state