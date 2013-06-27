#fog-flow
A python script for continuously storing case data gathered from an instance of Fog Creek's FogBugz
bug tracking service in a Cloudant database.

Cases from FogBugz are stored as json documents in the Cloudant distributed database service,
allowing for thorough cataloguing of case content and metadata for use in metrics tracking.

##Setup

Running fog-flow requires access to a Cloudant account and database.

If you do not have an account set up with Cloudant yet, visit https://cloudant.com/sign-up/
and create a free account.

Once the account is set up, you should create a database in Cloudant where your FogBugz data will reside.

Running fog-flow requires an accompanying config file, a template for which is included in the fog-flow github repo as flow.ini

Once you have a config file that follows this format (substituting the correct account info)
you should be able to run the script and begin tracking FogBugz cases. 

One thing to be sure of is that you have included to URL to the RSS feed for the specific FogBugz filter you wish to track cases with in your flow.ini file.

##Usage

NOTE: fog-flow is designed to run repeatedly in a scheduled manner, so that it is more or less continuously watching the target RSS feed
for case edits, we recommend accomplishing this via the unix `cron` command or another similiar task scheduler.

To run the script once, enter the following on the command line:

	python fogflow.py ./flow.ini

(if flow.ini isn't saved in the same directory as fogflow.py specify the correct filepath)#fog-flow
