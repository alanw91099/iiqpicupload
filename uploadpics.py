import json
import sys
import os
import time
import logzero
from logzero import logger
import requests
import urllib3

#### MODIFY BEFORE RUNNING ####
SITE_ID = "<your site id>"
TOKEN = "Bearer <your api token>"
BASE_URL = "<your org>.incidentiq.com"
PATH = "C:\\iiqpics\\"
###############################

logzero.logfile("logfile.log", disableStderrLogger=False)

def userlookup(id_number):
	url = "https://" + BASE_URL + "/api/v1.0/users/search/" + id_number
	payload = {}
	headers = {
	  'SiteID': SITE_ID,
	  'Authorization': TOKEN,
	  'Client': 'ApiClient'
	}

	response = requests.request("GET", url, headers=headers, data=payload)
	try:
		u = response.json()
	except:
		logger.error(f"API returned unknown info for {num} - rate limited?")
	try:
		if_exists = u['Items'][0]['UserId']
		if u['ItemCount'] == 1:
			return u['Items'][0]['UserId']
		else:
			return "duplicates"
	except:
		return "fail"

def uploadpic(id_number, userid):
	url = "https://" + BASE_URL + "/api/v1.0/profiles/" + userid + "/picture"
	filename = id_number + '.jpg'
	filepath = PATH + filename

	payload = {}
	files=[
	  ('File',(filename,open(filepath,'rb'),'image/jpeg'))
	]
	headers = {
	  'siteid': SITE_ID,
	  'Client': 'ApiClient',
	  'Authorization': TOKEN
	}

	response = requests.request("POST", url, headers=headers, data=payload, files=files)
	return response.status_code

def main():
	success = 0
	fail = 0
	allfiles = []
	l = os.listdir(PATH)

	for x in l:
		num = x.split('.')[0]
		allfiles.append(str(num))

	for num in allfiles:

		MAX_RETRIES = 5
		retries = 0

		while retries < MAX_RETRIES:
			
			try:
				userid = userlookup(num)
				if userid == "fail":
					logger.error(f"Looking up user {num} failed")
					break
				if userid == "duplicate":
					logger.error(f"Duplicates of user {num} found")
					break
				api = uploadpic(num, userid)
				if api == 200:
					logger.info(f"Uploaded {num} successfully")
					success = success + 1
				else:
					logger.error(f"Failed to upload {num}")
					fail = fail + 1
				#time.sleep(1)
			except urllib3.exceptions.SSLError as e:
				logger.error(f"SSL Error on {num}, retrying: {e}")
				retries += 1
				time.sleep(5)
				continue
			except requests.exceptions.ConnectionError as e:
				logger.error(f"Connection Error on {num}, retrying: {e}")
				retries += 1
				time.sleep(5)
				continue
			except Exception as e:
				logger.error(f"Unknown error on {num}, retrying: {e}")
				retries += 1
				time.sleep(5)
				continue
			break
		else:
			logger.error(f"Max retries reached for {num}, moving on")

	logger.warn(f"Uploaded {success} successfully, failed on {fail}")

if __name__ == "__main__":
    main()
