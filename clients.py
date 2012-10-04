pimport json
import urllib2
import re
from pprint import pprint
import logging
from pprint import pformat

username = "christochild"
password = "Peter02"
URL = "https://stream.twitter.com/1/statuses/sample.json"

password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None, "https://stream.twitter.com", username, password)
handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)

file_obj = opener.open(URL)

clients = {'web' : 0}

try:
	while 1:
		next = file_obj.readline()
		if not next:
			break
		data = json.loads(next)
		
		try:
			client = re.sub('<[^<]+?>', '', data["source"])
			if client in clients:
				clients[client] = clients[client] + 1
			else:
				clients[client] = 1
		except KeyError:
			client = ''

		print len(clients)

	print 'Completed'
except KeyboardInterrupt:
	print 'Interrupt'

print 'Saving file...'

myfile = open("clients.txt", "w")
myfile.write(pformat(clients) + '\n')
myfile.close

pprint(clients)