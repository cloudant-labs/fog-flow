

import json, time, xmltodict, fbSettings
from datetime import datetime
from fogbugz import FogBugz



def time_format(timestamp):     # format timestamp into datetime object
    if timestamp:
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").isoformat()
    else:
        return None



def toString(field):            # convert tag to string         
    if field.string:            # validate input field 
        return field.string.encode('UTF-8')
    else:
        return None



def get_email(evt):         # returns dict of email fields from an event
    if toString(evt.femail) == 'true':  # ONLY if email exists
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



def get_events(case):       # returns list of all events in a case.
    events = []
    for i in case.events.findAll('event'):
        event = {}
        event['_id'] = i['ixbugevent'].encode('UTF-8')
        event['name'] = toString(i.sperson)
        event['timestamp'] = time_format(toString(i.dt))
        event['description'] = toString(i.sverb)
        event['changes'] = toString(i.schanges)
        event['text'] = toString(i.s)
        event['email'] = get_email(i)
        events.append(event)

    return events



def get_person(case, ixevent):              # get the person's name from the latest occurance 
    for i in case.events.findAll('event'):  # of a particular type of event with the evt code
        if toString(i.evt) == ixevent:
            return toString(i.sperson)


def get_tags(case):     # returns a list of existing tags in a case
    li=[]
    for tag in case.tags:
        li.append(toString(tag))
    return li




def docBuilder(url, _id):       # building the actual document
    fb = FogBugz(url)
    fb.logon(fbSettings.USER_NAME, fbSettings.PASSWORD)

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
            'events' : get_events(case),

            ##### name/timestamp strings retrieved from loop below #####
            'opened' : {'ix' : int(toString(case.ixpersonopenedby)), 'by' : get_person(case,'1'),
                        'timestamp' : time_format(toString(case.dtopened))},
            'closed' : {'ix' : int(toString(case.ixpersonclosedby)), 'by' : get_person(case,'6'),
                        'timestamp' : time_format(toString(case.dtclosed))},
            'resolved' : {'ix' : int(toString(case.ixpersonresolvedby)), 'by' : get_person(case, '14'),
                        'timestamp' : time_format(toString(case.dtresolved))},
            'last_edited' : {'ix' : int(toString(case.ixpersonlasteditedby)),
                        'by' : toString(case.events.findAll('event')[-1].sperson),
                        'timestamp' : time_format(toString(case.dtlastupdated))}

            }



    fb.logoff() # log off from fogbugz

    return doc




