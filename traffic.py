#!/usr/bin/python

"""
Origin List:
http://services.my511.org/traffic/getoriginlist.aspx?token=af466849-ac4d-47be-9e81-1aa6e0ffdd9f

Destination List:
http://services.my511.org/traffic/getdestinationlist.aspx?token=af466849-ac4d-47be-9e81-1aa6e0ffdd9f&o=42

Path List:
http://services.my511.org/traffic/getpathlist.aspx?token=af466849-ac4d-47be-9e81-1aa6e0ffdd9f&o=42&d=1061


Origin Node: 42 (I-280S and US-101 S)
Destination Node: 1061 (I-280S and Sand Hill Road)
"""

import sys, getopt
import urllib2, urllib
from xml.dom import minidom

class Path:
	n = 0
	currentTravelTime = 0
	typicalTravelTime = 0
	miles = 0
	segments = []
	incidents = []

# input data

# from 511 - only works for SF Bay Area
base_url = 'http://services.my511.org/traffic/getpathlist.aspx'

def main(argv):
	token = 'af466849-ac4d-47be-9e81-1aa6e0ffdd9f'
	origin_id = '42'
	dest_id = '1061'

	try:
		opts, args = getopt.getopt(argv, "ht:o:d:",["token=","origin=","destination="])
	except getopt.GetoptError:
		print 'traffic.py -t token -o originid -d destinationid'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print 'traffic.py -t token -o originid -d destinationid'
			sys.exit()
		elif opt in ('-o', '--origin'):
			origin_id = arg
		elif opt in ('-d', '--destination'):
			dest_id = arg
		elif opt in ('-t', '--token'):
			token = token

	routes = getRoutes(token, origin_id, dest_id)
	printRoutes(sorted(routes, key=lambda route: route.currentTravelTime))

def getRoutes(t, o, d):

	data = {}
	data['o'] = o
	data['d'] = d
	data['token'] = t

	url_values = urllib.urlencode(data)

	actual_url = base_url + '?' + url_values

	# print 'url: %s' % actual_url

	# load the data
	data = urllib2.urlopen(actual_url)
	xmldoc = minidom.parse(data)
	data.close()

	# parse the xml

	xml_paths = xmldoc.getElementsByTagName("path")
	# print 'found %d paths' % xml_paths.length

	return parsePaths(xml_paths)

def parsePaths(xml_paths):
	paths = []
	n = 0
	for path in xml_paths:
		p = Path()
		p.currentTravelTime = path.getElementsByTagName('currentTravelTime')[0].childNodes[0].data
		p.typicalTravelTime = path.getElementsByTagName('typicalTravelTime')[0].childNodes[0].data
		p.miles = path.getElementsByTagName('miles')[0].childNodes[0].data
		p.n = n
		n = n + 1
		segments = path.getElementsByTagName('road')
	# 	print 'found %d segments' % segments.length
		p.segments = []
		for segment in segments:
			if not "Ramp" in segment.childNodes[0].data:
				p.segments.append(segment.childNodes[0].data)
		incidents = path.getElementsByTagName('incident')
		p.incidents = []
		for incident in incidents:
			p.incidents.append(incident.childNodes[0].data)

		paths.append(p)

	return paths

def printRoutes(paths):
	for p1 in paths:
		roads = p1.segments[0]
		for r in p1.segments[1:]:
			roads = roads + ', ' + r

		star = ''
		if (long(p1.currentTravelTime) / long(p1.typicalTravelTime)) > 1.1:
			star = '**'

		print '%sRoute %d (via %s):\n\ttime: %s mins (%s typical)\n\tdistance: %s miles' % (
			star,
			p1.n + 1,
			roads,
			p1.currentTravelTime,
			p1.typicalTravelTime,
			p1.miles)

		for incident in p1.incidents:
			print '\t***Incident: %s' % incident

if __name__ == "__main__":
	main(sys.argv[1:])