#!/usr/bin/env python 

import os, sys
import ConfigParser
import oauth2 as oauth
import json
import git

config = ConfigParser.ConfigParser()
config.read('config.ini')

prefix_path = os.path.dirname(os.path.realpath(__file__))
consumer = oauth.Consumer(key=config.get('OAuth', 'key'), secret=config.get('OAuth', 'secret'))
client = oauth.Client(consumer)
response = client.request('https://bitbucket.org/api/1.0/user/repositories/', 'GET')
if not response[0]['status'] == '200': sys.exit('could not authenticate. check oauth credentials!')
repos = json.loads(response[1])

state = {
		'dirty':   {'text': '========= Dirty =========', 'items': []},
		'pull':    {'text': '====== Pull Errors ======', 'items': []},
		'push':    {'text': '====== Push Errors ======', 'items': []},
		'unknown': {'text': '===== Unknown Repos =====', 'items': []},
		}

for dir in os.listdir(prefix_path):
	if not os.path.isdir(os.path.join(prefix_path, dir)): continue
	for subdir in os.listdir(os.path.join(prefix_path, dir)):
		if not os.path.isdir(os.path.join(prefix_path, dir, subdir)): continue
		state['unknown']['items'].append('%s/%s' % (dir, subdir))

for repo in repos:
	fullslug = '%s/%s' % (repo['owner'], repo['slug'])
	print 'syncing %s' % fullslug
	if fullslug in state['unknown']['items']: state['unknown']['items'].remove(fullslug)
	repo_path = os.path.join(prefix_path, repo['owner'], repo['slug'])
	
	if not os.path.exists(repo_path):
		os.makedirs(repo_path)
	
	try:
		gitrepo = git.Repo(repo_path)
	except:
		git.Repo.clone_from('git@bitbucket.org:%s/%s.git' % (repo['owner'], repo['slug']), repo_path)
		gitrepo = git.Repo(repo_path)
		
	if gitrepo.is_dirty():
		state['dirty']['items'].append(fullslug)
	
	try:    gitrepo.remotes.origin.pull()
	except:
		state['pull']['items'].append(fullslug)
		print "Unexpected pull error:", sys.exc_info()[0]
	
	try:    gitrepo.remotes.origin.push()
	except:
		state['push']['items'].append(fullslug)
		print "Unexpected push error:", sys.exc_info()[0]
	

for key, value in state.iteritems():
	if len(value['items']) > 0:
		print '\n%s' % value['text']
		for item in value['items']:
			print item
