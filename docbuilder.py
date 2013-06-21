import calendar
import ConfigParser
import json
import re
import time

from fogbugz import FogBugz
import requests
import xmltodict

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# convert fogbugz datetime into Unix timestamp
def unix_time(timestamp, format):
    if timestamp:
        return calendar.timegm(time.strptime(timestamp, format))
    else:
        return None


def get_rev(case_id, db_url, db_user, db_pass):
    r = requests.head(db_url + case_id,
                    auth=(db_user, db_pass))
    if r.status_code == 200 or r.status_code == 202:
        return r.headers['etag'].strip('"')
    else:
        return None


# collapse unwanted xml fields, revise names, reformat timestamps
def prune_doc(doc):
    doc = doc['response']['cases']['case']
    doc['events'] = doc['events']['event']
    del doc['@operations'], doc['ixpersonopenedby']
    del doc['ixpersonclosedby'], doc['ixpersonresolvedby']
    del doc['ixpersonlasteditedby'], doc['plugin_customfields']
    if doc['tags']:
        doc['tags'] = doc['tags']['tag']
    events = []
    for event in reversed(doc['events']):
        events.append(dict([(transform(key), value)
                     for key, value in event.items()]))
    for event in events:
        event['timestamp'] = unix_time(event['timestamp'], TIME_FORMAT)
        del event['fhtml'], event['_id'], event['bemail']
        del event['ixbugevent'], event['sformat'], event['ixperson']
        del event['ixpersonassignedto'], event['bexternal']
        if 'shtml' in event: del event['shtml']
    doc['events'] = events
    doc = dict([(transform(key), value) for key, value in doc.items()])
    doc['last_updated'] = unix_time(doc['last_updated'], TIME_FORMAT)
    doc['date_opened'] = unix_time(doc['date_opened'], TIME_FORMAT)
    doc['date_closed'] = unix_time(doc['date_closed'], TIME_FORMAT)
    doc['date_resolved'] = unix_time(doc['date_resolved'], TIME_FORMAT)
    print json.dumps(doc, indent=4, separators=(',', ': '))
    return doc


# substitute ambiguous key names from fb for preferable names for clarity
def transform(key):
    renamings = dict([('@ixbug', '_id'), ('ixpriority', 'priority'), 
                    ('ixrelatedbugs', 'related_cases'), ('stitle', 'title'),
                    ('dtopened', 'date_opened'), ('dtclosed', 'date_closed'),
                    ('spersonassignedto', 'assigned_to'), ('scc', 'cc'),
                    ('sstatus', 'status'), ('ixbugparent', 'parent_case'),
                    ('dtresolved', 'date_resolved'), ('sproject', 'project'),
                    ('sarea', 'area'), ('ixbugchildren', 'sub_cases'),
                    ('dtlastupdated', 'last_updated'), ('ssubject', 'subject'),
                    ('scategory', 'category'), ('events', 'events'),
                    ('@ixbugevent', 'event_id'), ('evt', 'event_code'),
                    ('sverb', 'event_type'),('dt', 'timestamp'), ('sto', 'to'),
                    ('s', 'event_text'), ('femail', 'is_email'),
                    ('fexternal', 'externally_triggered'), ('sfrom', 'from'),
                    ('schanges', 'changes'), ('rgattachments', 'attachments'),
                    ('evtdescription', 'event_description'), ('sperson', 'person'),
                    ('sbcc', 'bcc'), ('sreplyto', 'replyto'), ('sdate', 'send_date'),
                    ('sbodyhtml', 'body_html'), ('sbodytext', 'body_text')])
    # hack to get around gross FB api representation of custom fields
    if key.startswith('plugin_customfields_at_fogcreek_com_'):
        result = key.replace('plugin_customfields_at_fogcreek_com_', '')[:-2]
        ending = result[-1:]
        if re.match('[0-9]', ending):
            return result[:-2]
        else:
            return result[:-1]
    # end grossness
    if key in renamings.keys():
        return renamings[key]
    else:
        return key


def build(api_url, case_id, api_user, api_pass, db_url, db_user, db_pass):
    fb = FogBugz(api_url)
    fb.logon(api_user, api_pass)
    case = fb.search(q=str(case_id), cols='sTitle,dtOpened,dtClosed,ixPersonOpenedBy,ixPersonClosedBy,ixPersonResolvedBy,ixPersonLastEditedBy,ixRelatedBugs,sPersonAssignedTo,sStatus,ixPriority,tags,ixBugParent,ixBugChildren,dtResolved,dtClosed,dtLastUpdated,sProject,sArea,sCategory,events,plugin_customfields')
    doc = prune_doc(xmltodict.parse(str(case)))
    # add rev if the document is a revision
    rev = get_rev(doc['_id'], db_url, db_user, db_pass)
    if rev:
        doc['_rev'] = rev
    fb.logoff() # log off from fogbugz
    return doc
