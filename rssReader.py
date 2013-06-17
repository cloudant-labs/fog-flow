#!/usr/bin/env python
import feedparser, sys, time, calendar, uploader, docBuilder, fbSettings

# parse the global rss feed for the filter, creating a list of docs to create/update
def parse_rss(rss_url, last_run):
	# create a new parser from RSS feed
	fp = feedparser.parse(rss_url)
	# create list of cases needing update 
	updates = []
	for entry in fp.entries:
		timestamp = unixTime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")

		# if more recent than last run, this entry has an update
		if timestamp > last_run:
			case = entry.title.split(':')[0].lstrip('Case ')
			updates.append(case)
	return updates


# convert fogbugz rss date into Unix timestamp
def unixTime(timestamp, format):
	return calendar.timegm(time.strptime(timestamp, format))


if __name__=='__main__':
	rss_url = sys.argv[1]
	last_run = int(sys.argv[2])
	updates = parse_rss(rss_url, last_run)
	success = []
	for case_id in updates:
		# create the json
		# call to docBuilder function here
		json_doc = docBuilder.build(fbSettings.API_URL, case_id)
		print "uploading " + str(case_id)
  		u = uploader.upload(json_doc)
  		print u
  		if u:
  			success.append(u)
  	# success if lengths match (as many successes as docs)
  	print len(success) == len(updates)
  	### update last_run (or I suppose Cron handles this) ###