#!/usr/bin/env python

import calendar
import ConfigParser
import json
import sys
import time

import feedparser
import requests

import docbuilder

# to parse the global rss feed for the filter,
# creating a list of docs to create/update
def parse_rss(rss_url, last_run):
    # create a new parser from RSS feed
    fp = feedparser.parse(rss_url)
    # create list of cases needing update
    updates = []
    for entry in fp.entries:
        timestamp = docbuilder.unix_time(entry.published,
                                        "%a, %d %b %Y %H:%M:%S %Z")

        # if more recent than last run, this entry has an update
        if timestamp > last_run:
            case = entry.title.split(':')[0].lstrip('Case ')
            updates.append(case)
    return updates

# upload an individual json document
def upload(json_doc, db_url, db_user, db_pass):
    headers = {"content-type": "application/json"}
    resp = requests.post(db_url, auth=(db_user, db_pass),
                        data=json.dumps(json_doc),
                        headers=headers)
    # will return true if this upload was successful
    return resp.status_code in [201, 202]



# reads a Unix timestamp from a temp file representing the last time
# at which this script was run, then updates
# if no such file exists, returns Unix epoch as an integer (0)
def get_last_run(tempfile):
    try:
        # check for the file
        with open(tempfile, 'r') as json_data:    
            data = json.load(json_data)
            # obtain current state
            return int(data['last_run'])
    except IOError:
        return 0


# updates the timestamp by overwriting/creating the temp state file
def update_last_run(current_run, tempfile):
    with open(tempfile, 'w') as f:
        data = {}
        data['last_run'] = current_run
        json.dump(data, f)


# helper function for ConfigParser
def ConfigSectionMap(section, Config):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


def main():
    Config = ConfigParser.ConfigParser()
    Config.read("flow.ini")
    current_run = calendar.timegm(time.gmtime())
    rss_url = ConfigSectionMap("FogBugzAPI", Config)['rss_url']
    api_url = ConfigSectionMap("FogBugzAPI", Config)['api_url']
    api_user = ConfigSectionMap("FogBugzAPI", Config)['api_user']
    api_pass = ConfigSectionMap("FogBugzAPI", Config)['api_pass']
    db_url = ConfigSectionMap("Cloudant", Config)['db_url']
    db_user = ConfigSectionMap("Cloudant", Config)['db_user']
    db_pass = ConfigSectionMap("Cloudant", Config)['db_pass']
    tempfile = ConfigSectionMap("LastRun", Config)['tempfile']
    last_run = get_last_run(tempfile)
    for case_id in parse_rss(rss_url, last_run):
        json_doc = docbuilder.build(api_url, case_id, api_user, api_pass, db_url, db_user, db_pass)
        if not upload(json_doc, db_url, db_user, db_pass):
            sys.exit(1)
    update_last_run(current_run, tempfile)
    print "success"


if __name__=='__main__':
    main()
