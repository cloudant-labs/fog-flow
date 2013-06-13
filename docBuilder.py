import json
from datetime import datetime
import time
from fogbugz import FogBugz
import fbSettings


def time_format(from_time):
    dt = datetime.strptime(from_time, "%Y-%m-%dT%H:%M:%SZ")
    return dt.isoformat()




def docBuilder(url, _id):
  	
  	ENCODE_TYPE = 'UTF-8'



	fb = FogBugz(url)
 	fb.logon(fbSettings.EMAIL, fbSettings.PASSWORD)



	case = fb.search(q = _id, cols = 'sTitle,dtOpened,dtClosed,ixPersonOpenedBy,ixPersonClosedBy,ixPersonResolvedBy,ixPersonLastEditedBy,ixRelatedBugs,sPersonAssignedTo,ixPriority,CloudantUser,CloudantCluster,CloudantOrg,tags,ixBugParent,ixBugChildren,dtResolved,dtClosed,dtLastUpdated,sProject,sArea,sCategory,events,people')     

    


    # store tags into list
	tags = []
 	for i in case.tags:
   		tags.append(i.string.encode(ENCODE_TYPE))


    # store sub cases into list
  	sub_cases = []
 	for i in case.ixbugchildren:
   		sub_cases.append(i)


   	# store related cases into list
 	related_cases = []
 	if case.ixrelatedbugs.string:
 		for i in case.ixrelatedbugs.string.encode(ENCODE_TYPE).split(","):
   			related_cases.append(int(i))
    

	


    # document 
	doc = { '_id' : _id,
    		'title' : case.stitle.string.encode(ENCODE_TYPE),
        	'cloudant_user' : case.cloudantuser.string.encode(ENCODE_TYPE) if case.cloudantuser.string else None,
        	'cloudant_cluster' : case.cloudantcluster.string.encode(ENCODE_TYPE) if case.cloudantcluster.string else None,
        	'cloudant_org' : case.cloudantorg.string.encode(ENCODE_TYPE) if case.cloudantorg.string else None,
        	'area' : case.sarea.string.encode(ENCODE_TYPE),
       		'category' : case.scategory.string.encode(ENCODE_TYPE),
       		'related_cases' : related_cases,

            ##### name/timestamp strings retrieved from loop below #####
       		'opened' : {'ix' : int(case.ixpersonopenedby.string.encode(ENCODE_TYPE)),
                   		'timestamp' : time_format(case.dtopened.string.encode(ENCODE_TYPE))},
      		'closed' : {'ix' : int(case.ixpersonclosedby.string.encode(ENCODE_TYPE)),
                   		'timestamp' : time_format(case.dtclosed.string.encode(ENCODE_TYPE)) if case.dtclosed.string else None},
       		'resolved' : {'ix' : int(case.ixpersonresolvedby.string.encode(ENCODE_TYPE)),
                    	'timestamp' : time_format(case.dtresolved.string.encode(ENCODE_TYPE)) if case.dtresolved.string else None},

      		'last_edited' : {'ix' : int(case.ixpersonlasteditedby.string.encode(ENCODE_TYPE)),
                     	'timestamp' : time_format(case.dtlastupdated.string.encode(ENCODE_TYPE)) if case.dtlastupdated.string else None},       
            

       		'assignee' : case.spersonassignedto.string.encode(ENCODE_TYPE),
      		'assigned' : {"to" : case.spersonassignedto.string.encode(ENCODE_TYPE)},

       		'priority' : int(case.ixpriority.string.encode(ENCODE_TYPE)),
       		'tags' : tags,
     		'parent_case' : int(case.ixbugparent.string.encode(ENCODE_TYPE)),
      		'sub_cases' : sub_cases,
      		'project' : case.sproject.string.encode(ENCODE_TYPE),
            
       		'events' : []	

       		}




	
	event_array = case.events.findAll('event')

	for i in event_array:

		# retrieve names, timestamps for 'opened','closed','assigned',etc for top level fields
		ixevent = int(i.evt.string.encode(ENCODE_TYPE))

		if ixevent == 1:		# opened evt
			doc['opened']['by'] = i.sperson.string.encode(ENCODE_TYPE)
		if ixevent == 6:		# closed evt
			doc['closed']['by'] = i.sperson.string.encode(ENCODE_TYPE)
		if ixevent == 14:		# resolved evt
			doc['resolved']['by'] = i.sperson.string.encode(ENCODE_TYPE)
		if ixevent == 3:		# assigned evt
			doc['assigned']['timestamp'] = time_format(i.dt.string.encode(ENCODE_TYPE))

		# get the person of the last edited event
		if i == event_array[-1]:
			doc['last_edited']['by'] = i.sperson.string.encode(ENCODE_TYPE)




		# adding event history to 'events' field
		event = {}
 		event['_id'] = int(i['ixbugevent'])
 		event['name'] = i.sperson.string.encode(ENCODE_TYPE)
 		event['timestamp'] = time_format(i.dt.string.encode(ENCODE_TYPE))
 		event['description'] = i.sverb.string.encode(ENCODE_TYPE)
 		event['changes'] = i.schanges.string.encode(ENCODE_TYPE) if i.schanges.string else None
 		event['text'] = i.s.string.encode(ENCODE_TYPE) if i.s.string else None
  		event['email'] = {}

    	# only if email exists
 		if (i.femail.string.encode(ENCODE_TYPE) == 'true'):
  			event['email']['from'] = i.sfrom.string.encode(ENCODE_TYPE)
  			event['email']['to'] = i.sto.string.encode(ENCODE_TYPE)
  			event['email']['subject'] = i.ssubject.string.encode(ENCODE_TYPE) if i.ssubject.string else None
  			event['email']['body'] = i.sbodytext.string.encode(ENCODE_TYPE) if i.sbodytext.string else None
  			event['email']['cc'] = i.scc.string.encode(ENCODE_TYPE) if i.scc.string else None

    		# time shows exactly as it appears from the message. may be different for every message
  			event['email']['timestamp'] = (i.sdate.string.encode(ENCODE_TYPE))




  		doc['events'].append(event)



	



	fb.logoff()



	return doc





########################## TEST ##########################



url = 'https://cloudant.fogbugz.com/'
_id = 20302


d = docBuilder(url, _id)

# ouput json file
#with open('sample.json', 'w') as outfile:
# json.dump(d, outfile) 


sPersonAssignedTo
for item in d:
	sPersonAssignedTo str(item)+":"+'\t\t' + str(d[item]) 
sPersonAssignedTo



