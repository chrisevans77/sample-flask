print('Imported ga_measurement_protocol')


from urllib.parse import quote
import requests
import uuid

# Percent encode strings, to be passed to GA measurement protocol
def encode_string(string):
	encoded_string = quote(string, safe='')
	return encoded_string


def measurement_protocol_request(document_path, document_title, user_agent, t='pageview', cid=str(uuid.uuid4()), **kwargs):


	google_analytics_id_googlebot = 'UA-131262480-3'
	google_analytics_id = 'UA-131262480-4'


	if not user_agent.find("googlebot") == -1:
		request_url = f'https://www.google-analytics.com/collect?v=1&t={t}&tid={google_analytics_id_googlebot}&cid={cid}&dp={encode_string(document_path)}&dt={encode_string(document_title)}'

		for key in kwargs:
			request_url += '&' + key + '=' + encode_string(kwargs[key])
			
		r = requests.get(request_url)
	

	request_url = f'https://www.google-analytics.com/collect?v=1&t={t}&tid={google_analytics_id}&cid={cid}&dp={encode_string(document_path)}&dt={encode_string(document_title)}'

	for key in kwargs:
		request_url += '&' + key + '=' + encode_string(kwargs[key])

	r = requests.get(request_url)

	return


#print(measurement_protocol_request(document_path='/some-url', document_title='title with spaces', user_agent='Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)', cd1='custom dimension1', cm2='123', cd4='/*.'))
