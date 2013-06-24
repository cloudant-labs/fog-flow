#!/usr/bin/env python

import calendar
import ConfigParser
import json
import sys
import time

import feedparser
import requests

import docbuilder

def parse_rss(rss_url, last_run):
    fp = feedparser.parse(rss_url)
    updates = []
    for entry in fp.entries:
        timestamp = docbuilder.unix_time(
            entry.published,
            "%a, %d %b %Y %H:%M:%S %Z"
        )
        if timestamp > last_run:
            case = entry.title.split(':')[0].lstrip('Case ')
            updates.append(case)
    return updates


def upload(json_doc, db_url, db_user, db_pass):
    headers = {"content-type": "application/json"}
    resp = requests.post(
        db_url,
        auth=(db_user, db_pass),
        data=json.dumps(json_doc),
        headers=headers
    )
    return resp.status_code in [201, 202]


def get_last_run(tempfile):
    try:
        with open(tempfile, 'r') as json_data:    
            data = json.load(json_data)
            return int(data['last_run'])
    except IOError:
        return 0


def update_last_run(current_run, tempfile):
    with open(tempfile, 'w') as f:
        data = {}
        data['last_run'] = current_run
        json.dump(data, f)


def main(configfile):
    config = ConfigParser.RawConfigParser()
    config.read(configfile)
    current_run = calendar.timegm(time.gmtime())
    rss_url = config.get('FogBugz', 'rss_url')
    api_url = config.get('FogBugz', 'api_url')
    api_user = config.get("FogBugz", 'api_user')
    api_pass = config.get("FogBugz", 'api_pass')
    db_url = config.get("Cloudant", 'db_url')
    db_user = config.get("Cloudant", 'db_user')
    db_pass = config.get("Cloudant", 'db_pass')
    tempfile = config.get("LastRun", 'tempfile')
    last_run = get_last_run(tempfile)
    for case_id in parse_rss(rss_url, last_run):
        json_doc = docbuilder.build(
            api_url,
            case_id,
            api_user,
            api_pass,
            db_url,
            db_user,
            db_pass
        )
        if not upload(json_doc, db_url, db_user, db_pass):
            sys.exit(1)
    print "successful"
    update_last_run(current_run, tempfile)


if __name__=='__main__':
    configfile = sys.argv[1]
    main(configfile)



