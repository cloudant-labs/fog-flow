import calendar
import json
import time

from fogbugz import FogBugz
import requests
import xmltodict

import fbsettings

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# convert fogbugz rss date into Unix timestamp
def unix_time(timestamp, format):
    if timestamp:
        return calendar.timegm(time.strptime(timestamp, format))
    else:
        return None


def to_string(field):
    if field.string:
        return field.string.encode('UTF-8')
    else:
        return None


def get_rev(case_id):
    r = requests.head(fbsettings.DB_URL + case_id, auth=(fbsettings.DB_USER, fbsettings.DB_PASS))
    if r.status_code == 200 or r.status_code == 202:
        return r.headers['etag'].strip('"')
    else:
        return None


# return dict of email fields from an event
def get_email(evt):
    if to_string(evt.femail):
        email = {}
        email['from'] = to_string(evt.sfrom)
        email['to'] = to_string(evt.sto)
        email['subject'] = to_string(evt.ssubject)
        email['body'] = to_string(evt.sbodytext)
        email['cc'] = to_string(evt.scc)
        email['timestamp'] = to_string(evt.sdate)
        return email
    else:
        return None


# returns a list of the event history for a given case
def get_events(case_id, fb):
  # request for events on given case
  respBugEvents = fb.search(q=case_id, cols='events')
  events = xmltodict.parse(str(respBugEvents))
  events = events['response']['cases']['case']
  events = events['events']['event']
  return events


# get the person's name from the latest occurance
# of a particular type of event with the evt code
def get_person(case, ixevent):
    for i in case.events.findAll('event'):
        if to_string(i.evt) == ixevent:
            return to_string(i.sperson)


def get_tags(case):
    return [to_string(tag) for tag in case.tags]


# building the actual document
def build(url, case_id):
    # case_id must be in 'gb:####' format
    fb = FogBugz(url)
    fb.logon(fbsettings.API_USER, fbsettings.API_PASS)

    case = fb.search(q = str(case_id).strip("fb:"), cols = 'sTitle,dtOpened,dtClosed,ixPersonOpenedBy,ixPersonClosedBy,ixPersonResolvedBy,ixPersonLastEditedBy,ixRelatedBugs,sPersonAssignedTo,sStatus,ixPriority,CloudantUser,CloudantCluster,CloudantOrg,tags,ixBugParent,ixBugChildren,dtResolved,dtClosed,dtLastUpdated,sProject,sArea,sCategory,events')
    
    # document (dict in JSON format)
    doc = { '_id' : case_id,
            'title' : to_string(case.stitle),
            'cloudant_user' : to_string(case.cloudantuser),
            'cloudant_cluster' : to_string(case.cloudantcluster),
            'cloudant_org' : to_string(case.cloudantorg),
            'area' : to_string(case.sarea),
            'category' : to_string(case.scategory),
            'assignee' : to_string(case.spersonassignedto),
            'assigned' : {'to' : to_string(case.spersonassignedto)},
            'priority' : int(to_string(case.ixpriority)),
            'tags' : get_tags(case),
            'sub_cases' : to_string(case.ixbugchildren).split(",") if to_string(case.ixbugchildren) else None,
            'related_cases' : to_string(case.ixrelatedbugs).split(",") if to_string(case.ixrelatedbugs) else None,
            'parent_case' : to_string(case.ixbugparent),
            'project' : to_string(case.sproject),
            'status' : to_string(case.sstatus),
            'events' : get_events(case_id, fb),
            'opened' : {'by' : get_person(case,'1'),
                        'timestamp' : unix_time(to_string(case.dtopened), TIME_FORMAT)},
            'closed' : {'by' : get_person(case,'6'),
                        'timestamp' : unix_time(to_string(case.dtclosed), TIME_FORMAT)},
            'resolved' : {'by' : get_person(case, '14'),
                        'timestamp' : unix_time(to_string(case.dtresolved), TIME_FORMAT)},
            'last_edited' : {'by' : to_string(case.events.findAll('event')[-1].sperson),
                        'timestamp' : unix_time(to_string(case.dtlastupdated), TIME_FORMAT)}
            }
    # add rev if the document is a revision
    rev = get_rev(doc['_id'])
    if rev:
        doc['_rev'] = rev

    fb.logoff() # log off from fogbugz
    return doc
