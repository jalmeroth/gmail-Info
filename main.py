#!/usr/bin/python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('main')
import argparse
import sys
import json
import urllib
import requests

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
	
	def getDomainsFromMsg(self, msgId, domains = None):
		"""docstring for getDomainsFromMsg"""
		data = self.getMessage(msgId)
		domains = domains or {}
		if 'payload' in data:
			if 'headers' in data['payload']:
				old_mail = None
				for header in data['payload']['headers']:
					mail = header.get('value').rstrip('>') # example@gmail.com
					if mail != old_mail: # de-duplication
						domain = mail[(mail.index('@')+1)::] # gmail.com
						# TODO: fix counters, if sender == x-original-sender
						if domain in domains:
							domains[domain]['count'] += 1 # increment counter
						else:
							domains[domain] = {'count': 1} # initialize dict
					else:
						logger.info('Found duplicate: ' + str(data['payload']['headers']))
					old_mail = mail
		return domains

	def getMessage(self, msgId):
		"""docstring for getMessage"""
		logger.info('Retrieving message: ' + str(msgId))
		
		url = 'https://www.googleapis.com/gmail/v1/users/{0}/messages/{1}'.format(self.userId, msgId)
		params = {
			'format': 'metadata',
			'metadataHeaders': ['Sender','X-Original-Sender']
		}
		url += '?' + urllib.urlencode(params, doseq=True)
		logger.info('URL:' + url)
		
		result = self.auth.signedRequest(url, self.userId)
		data = result.json()
		return data
	
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

def queryMX(domain):
	url = 'http://api.statdns.com/{0}/mx'.format(domain)
	r = requests.get(url)
	if r.status_code == requests.codes.ok:
		result = r.json()
		records = {}
		if 'answer' in result:
			for record in result['answer']:
				rdata = record.get('rdata', '').split(' ')
				weight = rdata[0]
				hostname = rdata[1]
				if weight and hostname:
					records[hostname] = {'weight': weight}
		if 'additional' in result:
			for record in result['additional']:
				recordType = record.get('type')
				hostname = record.get('name')
				# A-record holding IPv4 for host in records
				if recordType == 'A' and hostname in records:
					address = record.get('rdata')
					records[hostname].update({
						'address': address
					})
		return records

def main():
	"""docstring for main"""
	# initialize Arg-parser
	parser = argparse.ArgumentParser()
	# setup Arg-parser
	parser.add_argument('-u', '--user', type=str, help='User ID')
	# initialize args
	args = sys.argv[1:]
	# parse arguments
	args, unknown = parser.parse_known_args(args)
	logger.debug("args: " + str(args) + " unknown: " + str(unknown))
	
	if args.user:
		inf = gmailInfo(args.user)
		domains = {}
		for msg in inf.msgs:
			domains = inf.getDomainsFromMsg(msg.get('id'), domains)
		print json.dumps(domains)
		for domain in domains:
			domains[domain]['records'] = queryMX(domain)
		print json.dumps(domains)
	
if __name__ == '__main__':
	try:
		main()
	except (KeyboardInterrupt, SystemExit):
		print "Quitting."