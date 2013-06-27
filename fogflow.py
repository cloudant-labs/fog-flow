#!/usr/bin/env python

import calendar
import ConfigParser
import json
from optparse import OptionParser
import sys
import time

import feedparser
from fogbugz import FogBugz
import requests
import xmltodict

FB_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

rss_url = None
api_url = None
db_url = None
api_user = None
db_user = None
api_pass = None
db_pass = None
fb =  None


def unix_time(timestamp, format):
    if timestamp:
        return calendar.timegm(time.strptime(timestamp, format))
    else:
        return None

def get_rev(case_id):
    r = requests.head(
        db_url + case_id,
        auth=(db_user, db_pass)
    )
    if r.status_code == 200:
        return r.headers['etag'].strip('"')
    else:
        return None

def prune_doc(doc):
    excludekeys = [
        '@operations', 'ixpersonopenedby', 'ixpersonclosedby',
        'ixpersonresolvedby', 'ixpersonlasteditedby', 'plugin_customfields'
    ]
    d = dict([(
        transform(key), value)
        for key, value in doc['response']['cases']['case'].items()
        if key not in excludekeys
    ])
    if d['tags']:
        d['tags'] = d['tags']['tag']
    d['events'] = [prune_event(e) for e in d['events']['event']]
    d['last_updated'] = unix_time(d['last_updated'], FB_TIME_FORMAT)
    d['date_opened'] = unix_time(d['date_opened'], FB_TIME_FORMAT)
    d['date_closed'] = unix_time(d['date_closed'], FB_TIME_FORMAT)
    d['date_resolved'] = unix_time(d['date_resolved'], FB_TIME_FORMAT)
    return d

def prune_event(event):
    excludekeys = [
        'ixbugevent', 'ixpersonassignedto', 'shtml', 'fhtml', 'smessageid',
        '@ixbug', 'bemail', 'sformat', 'ixperson', 'bexternal'
    ]
    e = dict([
        (transform(key), value)
        for key, value in event.items()
        if key not in excludekeys
    ])
    e['timestamp'] = unix_time(e['timestamp'], FB_TIME_FORMAT)
    return e

def transform(key):
    renamings = {
        '@ixbug': '_id', 'ixpriority': 'priority',
        'ixrelatedbugs': 'related_cases', 'stitle': 'title',
        'dtopened': 'date_opened', 'dtclosed': 'date_closed',
        'spersonassignedto': 'assigned_to', 'scc': 'cc',
        'sstatus': 'status', 'ixbugparent': 'parent_case',
        'dtresolved': 'date_resolved', 'sproject': 'project',
        'sarea': 'area', 'ixbugchildren': 'sub_cases',
        'dtlastupdated': 'last_updated', 'ssubject': 'subject',
        'scategory': 'category', 'events': 'events',
        '@ixbugevent': 'event_id', 'evt': 'event_code',
        'sverb': 'event_type', 'dt': 'timestamp',
        'sto': 'to', 's': 'event_text', 'femail': 'is_email',
        'fexternal': 'externally_triggered', 'sfrom': 'from',
        'schanges': 'changes', 'rgattachments': 'attachments',
        'evtdescription': 'event_description', 'sperson': 'person',
        'sbcc': 'bcc', 'sreplyto': 'replyto', 'sdate': 'send_date',
        'sbodyhtml': 'body_html', 'sbodytext': 'body_text'
    }
    """
    The FB api does not yet have a method of returning the
    literal values of user defined keys, and returns user-defined custom fields
    in a poor format in which whitespace is represented as 'x', however any
    'x' characters in the key itself are not escaped, leading to some ambiguity
    This is an attempt to clean up some of these fields, but is likely to fail
    in several cases involving multiple 'x' chars in a key

    FB 9.0 promises a list_custom_fields function in its XML API, but have
    to wait until then...
    """ 
    # remove leading fogcreek labels
    if key.startswith('plugin_customfields_at_fogcreek_com_'):
        result = key.replace(
            'plugin_customfields_at_fogcreek_com_', '')[:-2].replace('x', '_')
        if "__" in result:
            result = result.replace('__', '_x')
        # remove trailing characters on key
        if result[-1:].isdigit():
            return result[:-2]
        else:
            return result[:-1]
    if key in renamings.keys():
        return renamings[key]
    else:
        return key

def build_doc(case_id):
    case = fb.search(
        q=str(case_id),
        cols=(
            'sTitle,dtOpened,dtClosed,ixPersonOpenedBy,ixPersonClosedBy,'
            'ixPersonResolvedBy,ixPersonLastEditedBy,ixRelatedBugs,'
            'sPersonAssignedTo,sStatus,ixPriority,tags,ixBugParent,'
            'ixBugChildren,dtResolved,dtClosed,dtLastUpdated,sProject,'
            'sArea,sCategory,events,plugin_customfields'
        )
    )
    doc = prune_doc(xmltodict.parse(str(case)))
    rev = get_rev(doc['_id'])
    if rev:
        doc['_rev'] = rev
    return doc

def parse_rss(last_run):
    fp = feedparser.parse(rss_url)
    updates = []
    for entry in fp.entries:
        timestamp = unix_time(
            entry.published,
            "%a, %d %b %Y %H:%M:%S %Z"
        )
        if timestamp > last_run:
            case = entry.title.split(':')[0].lstrip('Case ')
            updates.append(case)
    return updates

def upload_doc(json_doc):
    print "up"
    headers = {"content-type": "application/json"}
    resp = requests.post(
        db_url,
        auth=(db_user, db_pass),
        data=json.dumps(json_doc),
        headers=headers
    )
    return resp.status_code in [201, 202]

def most_recent_case():
    case = xmltodict.parse(str(fb.search(
        q='opened:"-7d.." orderby:dateopened',
        max=1
    )))
    return int(case['response']['cases']['case']['@ixbug'])

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

def upload_range(startcase, endcase):
    for case_id in range(startcase, endcase):
        case = fb.search(q=case_id)
        if int(xmltodict.parse(str(case))['response']['cases']['@count']) > 0:
            json_doc = build_doc(case_id)
            if not upload_doc(json_doc):
                sys.exit(1)

def main():
    global fb, db_url, db_user, db_pass, api_url, api_user, api_pass, rss_url
    current_run = calendar.timegm(time.gmtime())
    optparser = OptionParser()
    optparser.add_option(
        '-c',
        dest='config_file',
        help='config file path',
        default='./flow.ini'
    )
    optparser.add_option(
        '-a',
        '--allcases',
        action='store_true',
        dest='allcases',
        default=False, 
        help='force upload of all fb cases that exist, may take a long time'
    )
    optparser.add_option(
        '-r',
        '--range',
        type='int',
        nargs=2,
        dest='rangeupload',
        default=False,
        help='upload all cases in the specified range of '
                'case IDs in addition to any new edits'
    )
    (options, args) = optparser.parse_args()

    config = ConfigParser.RawConfigParser()
    config.read(options.config_file)
    rss_url = config.get('FogBugz', 'rss_url')
    api_url = config.get('FogBugz', 'api_url')
    api_user = config.get("FogBugz", 'api_user')
    api_pass = config.get("FogBugz", 'api_pass')
    db_url = config.get("Cloudant", 'db_url')
    db_user = config.get("Cloudant", 'db_user')
    db_pass = config.get("Cloudant", 'db_pass')
    tempfile = config.get("LastRun", 'tempfile')

    fb = FogBugz(api_url)
    fb.logon(api_user, api_pass)
    
    last_run = get_last_run(tempfile)
    # -a
    if (options.allcases):
        num_cases = most_recent_case()
        upload_range(1, num_cases + 1)
        update_last_run(current_run, tempfile)
    # default
    else:
        for case_id in parse_rss(last_run):
            json_doc = build_doc(case_id)
            if not upload_doc(json_doc):
                sys.exit(1)
        # -r
        if (options.rangeupload):
            upload_range(options.rangeupload[0], options.rangeupload[1] + 1)
        update_last_run(current_run, tempfile)

if __name__=='__main__':
    main()

