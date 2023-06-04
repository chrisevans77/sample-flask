# Function to log DeepCrawl API requests to Google Analytics using the measurement protocol
# https://developers.google.com/analytics/devguides/collection/protocol/v1

import requests
import uuid

def measurement_protocol_post(api_path, request_type, account_id):

	headers={'User-Agent': 'dc-connector'}

	data = {
				'tid': 'UA-86815099-9',
				'v': '1',
				't': 'pageview',
				'cid': str(uuid.uuid4()),
				'dp': api_path,
				'dt': request_type,
				'cd1': account_id
				'cd2': environment

	}

	request_url = 'https://www.google-analytics.com/collect'

	r = requests.post(request_url, data=data, headers=headers)

	return r.status_code



# Example usage. 
# The api_path contains the API URL we're requesting
# The reqest_type lets us include a label for the type of API request we're making
# The account_id lets us see how many requests we're making for each account
measurement_protocol_post(api_path='/some-api-url12', request_type='get project list', account_id='19')
