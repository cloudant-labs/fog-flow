#!/usr/local/bin/python
import calendar
import json
import sys
import time

import feedparser 

import docBuilder
import fbSettings
import uploader

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


# reads a Unix timestamp from a temp file representing the last time
# at which this script was run, then updates
# if no such file exists, returns Unix epoch as an integer (0)
def get_last_run():
    try:
        # check for the file
        with open('/tmp/fog-flow-state.json'):
            json_data = open('/tmp/fog-flow-state.json', 'r')
            data = json.load(json_data)
            # obtain current state
            last_run = data['last_run']
            # update state to reflect new execution
            json_data.close()
            return int(last_run)
    except IOError:
        return 0


# updates the timestamp by overwriting/creating the temp state file
def update_last_run():
    f = open('/tmp/fog-flow-state.json', 'w')
    data = {}
    data['last_run'] = calendar.timegm(time.gmtime())
    f.write(json.dumps(data))


# convert fogbugz rss date into Unix timestamp
def unixTime(timestamp, format):
    return calendar.timegm(time.strptime(timestamp, format))


if __name__=='__main__':
    rss_url = fbSettings.RSS_URL
    last_run = get_last_run()
    for case_id in parse_rss(rss_url, last_run):
        json_doc = docBuilder.build(fbSettings.API_URL, case_id)
        print "uploading " + str(case_id)
        if not uploader.upload(json_doc):
            sys.exit(1)
    update_last_run()