import calendar
import ConfigParser
import json
import re
import time

from fogbugz import FogBugz
import requests
import xmltodict

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

def unix_time(timestamp, format):
    if timestamp:
        return calendar.timegm(time.strptime(timestamp, format))
    else:
        return None


def get_rev(case_id, db_url, db_user, db_pass):
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
    d['last_updated'] = unix_time(d['last_updated'], TIME_FORMAT)
    d['date_opened'] = unix_time(d['date_opened'], TIME_FORMAT)
    d['date_closed'] = unix_time(d['date_closed'], TIME_FORMAT)
    d['date_resolved'] = unix_time(d['date_resolved'], TIME_FORMAT)
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
    e['timestamp'] = unix_time(e['timestamp'], TIME_FORMAT)
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
        # remove odd character sequence at end of key
        if result[-1:].isdigit():
            return result[:-2]
        else:
            return result[:-1]
    if key in renamings.keys():
        return renamings[key]
    else:
        return key


def build(api_url, case_id, api_user, api_pass, db_url, db_user, db_pass):
    fb = FogBugz(api_url)
    fb.logon(api_user, api_pass)
    case = fb.search(
        q=str(case_id),
        cols='sTitle,dtOpened,dtClosed,ixPersonOpenedBy,ixPersonClosedBy,'
        'ixPersonResolvedBy,ixPersonLastEditedBy,ixRelatedBugs,'
        'sPersonAssignedTo,sStatus,ixPriority,tags,ixBugParent,'
        'ixBugChildren,dtResolved,dtClosed,dtLastUpdated,sProject,'
        'sArea,sCategory,events,plugin_customfields'
    )
    doc = prune_doc(xmltodict.parse(str(case)))
    rev = get_rev(doc['_id'], db_url, db_user, db_pass)
    if rev:
        doc['_rev'] = rev
    fb.logoff()
    print json.dumps(doc, indent=4, separators=(",", "; "))
    return doc

