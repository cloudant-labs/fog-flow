# upload a single json document to remote database
import json, requests, fbSettings

def upload(json_doc):
	headers = {"content-type": "application/json"}
	resp = requests.post(fbSettings.DB_URL, auth=(fbSettings.DB_USER, fbSettings.DB_PASS), data=json.dumps(json_doc), headers=headers)
	# will return true if this upload was successful
	print resp
	return resp.status_code < 300