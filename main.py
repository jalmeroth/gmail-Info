#!/usr/bin/python
import logging
# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('main')
import json
import urllib
# import dnspython

from helpers import load, save
from oauth2.auth import Authenticator


class gmailInfo(object):
	"""docstring for gmailInfo"""
	def __init__(self, userId):
		super(gmailInfo, self).__init__()
		
		self.userId = userId
		self.file_prefs = 'client_secret.json'
		self.file_msgs = 'messages_{0}.json'.format(self.userId)
		
		self._prefs = load(self.file_prefs)
		self._msgs = load(self.file_msgs)
		
		clientId = self.prefs.get('client_id')
		clientSecret = self.prefs.get('client_secret')
		scope = ['https://www.googleapis.com/auth/gmail.readonly']
		tokens = self.prefs.get('tokens', {})
		self.auth = Authenticator(clientId, clientSecret, scope, tokens)
	
	def __del__(self):
		"""docstring for __del__"""
		self._prefs['tokens'] = self.auth.tokens
		self.prefs = self._prefs
		self.msgs = self._msgs
	
	def getMessage(self):
		"""docstring for getMessage"""
		logger.info('Retrieving message: ' + str(msgId))
		
		url = 'https://www.googleapis.com/gmail/v1/users/{0}/messages/{1}'.format(userId, msgId)
		params = {
			'format': 'metadata',
			'metadataHeaders': ['Sender','X-Original-Sender']
		}
		url += '?' + urllib.urlencode(params, doseq=True)
		logger.info('URL:' + url)
		
		result = auth.signedRequest(url, userId)
		data = result.json()
		
		if 'payload' in data:
			if 'headers' in data['payload']:
				for header in data['payload']['headers']:
					mail = header.get('value').rstrip('>') # example@gmail.com
					domain = mail[(mail.index('@')+1)::] # gmail.com
					# TODO: fix counters, if sender == x-original-sender
					if domain in domains:
						domains[domain]['count'] += 1 # increment counter
					else:
						domains[domain] = {'count': 1} # initialize dict
	
	def listMessages(self):
		"""docstring for listMessages"""
		url = 'https://www.googleapis.com/gmail/v1/users/{0}/messages'.format(self.userId)
		result = self.auth.signedRequest(url, self.userId)
		data = result.json()
		messages = data.get('messages', [])
		i = 0
	
		while ('nextPageToken' in data):
			
			i += 1 # increment counter
			
			params = {
				'pageToken': data.get('nextPageToken')
			}
			
			nextUrl = url + '?' + urllib.urlencode(params)
			logger.info('nextUrl:' + nextUrl)
			
			result = self.auth.signedRequest(nextUrl, self.userId)
			data = result.json()
			messages.extend(data.get('messages', []))
			
			if i == 100: # save state to file
				self.msgs = messages
				i = 0
		
		print "Items found:", len(messages)
		self.msgs = messages
	
	@property
	def prefs(self):
		"""docstring for prefs"""
		return self._prefs
	
	@prefs.setter
	def prefs(self, val):
		"""docstring for prefs"""
		return save(val, self.file_prefs)
	
	@property
	def msgs(self):
		"""docstring for msgs"""
		return self._msgs
	
	@msgs.setter
	def msgs(self, val):
		"""docstring for prefs"""
		self._msgs = val
		return save(val, self.file_msgs)

def main():
	"""docstring for main"""
	inf = gmailInfo('jan@almeroth.com')
	prefs = inf.prefs
	messages = inf.msgs
	# inf.listMessages()
	
	print len(messages)
	
if __name__ == '__main__':
	main()