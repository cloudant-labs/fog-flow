#fog-flow
A python script for storing case data gathered from an instance of Fog Creek's FogBugz
bug tracking service in a Cloudant database.

Cases from FogBugz are stored as json documents in the Cloudant distributed database service,
allowing for thorough cataloguing of case content and metadata for use in metrics tracking.

##Setup

First of all, there are a few required python libraries:

     $ pip install feedparser fogbugz requests ujson xmltodict

Running fog-flow requires access to a Cloudant account and database:

1. Visit https://cloudant.com/sign-up/ to create a free account.
2. After the account is set up, create a database in Cloudant where FogBugz data will reside.
3. fog-flow requires a config file, a template for which can be found as flow.ini, follow this format in creating your own

##Usage

NOTE: fog-flow is designed to run repeatedly in a scheduled manner, so that it is more or less continuously watching the target RSS feed
for case edits, this can be done via the unix `cron` (https://en.wikipedia.org/wiki/Cron) command or another similiar task scheduler.

###First run

Before fog-flow can reliably track new edits to cases, it first needs to upload all of the previously existing cases in FogBugz.

To upload all documents that exist run

    $ python fogflow.py -a

Be aware that this startup operation can take a long time to complete, depending on the number of cases in your FogBugz history

If it isn't necessary for you to track old cases, you can skip this step

###Getting it up and running

Running normally is as simple as calling

    $ python fogflow.py

on a scheduled basis in order to continuously check for new updates to cases; 
as mentioned before `cron` works well for this
