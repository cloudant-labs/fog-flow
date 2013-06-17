import json, time, fbSettings, requests, calendar, xmltodict
from fogbugz import FogBugz

# iso format found in fb
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# convert fogbugz time format into Unix timestamp
def unix_time(timestamp):
    if timestamp:
        return calendar.timegm(time.strptime(timestamp, TIME_FORMAT))
    else:
        return None

# convert tag to string
def toString(field): 
    if field.string:
        return field.string.encode('UTF-8')
    else:
        return None


# returns the _rev of a given doc (if it exists)
def get_rev(_id):
    r = requests.head(fbSettings.DB_URL + _id, auth=(fbSettings.DB_USER, fbSettings.DB_PASS))
    if r.status_code < 300:
        return r.headers['etag'].strip('"')
    else:
        return None


# returns dict of email fields from an event
def get_email(evt):         
    if toString(evt.femail):  # ONLY if email exists
        email = {}
        email['from'] = toString(evt.sfrom)
        email['to'] = toString(evt.sto)
        email['subject'] = toString(evt.ssubject)
        email['body'] = toString(evt.sbodytext)
        email['cc'] = toString(evt.scc)
        email['timestamp'] = toString(evt.sdate)
        return email
    else:
        return None


# and other essential info
def get_events(_id, fb):
  # request for events on given case
  respBugEvents = fb.search(q=_id, cols='events')
  events = xmltodict.parse(str(respBugEvents))
  events = events['response']['cases']['case']
  events = events['events']['event']
  return events


def get_person(case, ixevent):              # get the person's name from the latest occurance 
    for i in case.events.findAll('event'):  # of a particular type of event with the evt code
        if toString(i.evt) == ixevent:
            return toString(i.sperson)


# returns a list of existing tags in a case
def get_tags(case):
    li = []
    for tag in case.tags:
        li.append(toString(tag))
    return li

# building the actual document
def build(url, _id):
    # _id must be in 'gb:####' format
    fb = FogBugz(url)
    fb.logon(fbSettings.API_USER, fbSettings.API_PASS)

    case = fb.search(q = str(_id).strip("fb:"), cols = 'sTitle,dtOpened,dtClosed,ixPersonOpenedBy,ixPersonClosedBy,ixPersonResolvedBy,ixPersonLastEditedBy,ixRelatedBugs,sPersonAssignedTo,sStatus,ixPriority,CloudantUser,CloudantCluster,CloudantOrg,tags,ixBugParent,ixBugChildren,dtResolved,dtClosed,dtLastUpdated,sProject,sArea,sCategory,events')
    
    # document (dict in JSON format) 
    doc = { '_id' : _id,
            'title' : toString(case.stitle),
            'cloudant_user' : toString(case.cloudantuser),
            'cloudant_cluster' : toString(case.cloudantcluster),            
            'cloudant_org' : toString(case.cloudantorg),
            'area' : toString(case.sarea),
            'category' : toString(case.scategory),
            'assignee' : toString(case.spersonassignedto),
            'assigned' : {'to' : toString(case.spersonassignedto)},
            'priority' : int(toString(case.ixpriority)),
            'tags' : get_tags(case),
            'sub_cases' : toString(case.ixbugchildren).split(",") if toString(case.ixbugchildren) else None,
            'related_cases' : toString(case.ixrelatedbugs).split(",") if toString(case.ixrelatedbugs) else None,
            'parent_case' : toString(case.ixbugparent),
            'project' : toString(case.sproject),
            'status' : toString(case.sstatus),
            'events' : get_events(_id, fb),
            'opened' : {'ix' : int(toString(case.ixpersonopenedby)), 'by' : get_person(case,'1'),
                        'timestamp' : unix_time(toString(case.dtopened))},
            'closed' : {'ix' : int(toString(case.ixpersonclosedby)), 'by' : get_person(case,'6'),
                        'timestamp' : unix_time(toString(case.dtclosed))},
            'resolved' : {'ix' : int(toString(case.ixpersonresolvedby)), 'by' : get_person(case, '14'),
                        'timestamp' : unix_time(toString(case.dtresolved))},
            'last_edited' : {'ix' : int(toString(case.ixpersonlasteditedby)),
                        'by' : toString(case.events.findAll('event')[-1].sperson),
                        'timestamp' : unix_time(toString(case.dtlastupdated))}
            }
    # add _rev if the document is a revision    
    _rev = get_rev(doc['_id'])
    if _rev is not None:
        doc['_rev'] = _rev

    fb.logoff() # log off from fogbugz
    return doc