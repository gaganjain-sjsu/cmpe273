import logging
logging.basicConfig(level=logging.DEBUG)

from spyne import Application, srpc, ServiceBase, \
	Integer, Unicode

from spyne import Iterable

from spyne.protocol.http import HttpRpc
from spyne.protocol.json import JsonDocument

from spyne.server.wsgi import WsgiApplication
import requests,collections

class HelloWorldService(ServiceBase):
	@srpc(Unicode,Unicode,Unicode, _returns=Iterable(Unicode))
	def check_crime(lat, lon, rad):
		  resp = {"total_crime": 0, "the_most_dangerous_streets" : [], "crime_type_count" : {}, "event_time_count" : {}}
		  total_count = 0
		  crime_type = {}   
		  event_time = {"12:01am-3am" : 0, "3:01am-6am" : 0,"6:01am-9am" : 0,"9:01am-12noon" : 0,"12:01pm-3pm" : 0,"3:01pm-6pm" : 0,"6:01pm-9pm" : 0,"9:01pm-12midnight" : 0}

		  r = requests.get("https://api.spotcrime.com/crimes.json?lat=" + lat + "&lon=" + lon + "&radius=" + rad + "&key=.")
		  crimeJson =  r.json()  # fetches the response in json format

		  #return r
		  #yield crimeJson

		  d = collections.defaultdict(int)
		  addressSet = []
		  for crime in crimeJson["crimes"]:
				address = crime["address"]

				if address.find("BLOCK OF") >0:
					index = address.find("BLOCK OF")
					street = address[index+8:]
					addressSet.append(street)

				elif address.find("BLK") > 0:
					index = address.find("BLK")
					street = address[index+3:]
					addressSet.append(street)

				elif address.find("BLOCK") > 0:
					index = address.find("BLOCK")
					street = address[index+8:]
					addressSet.append(street)

				elif address.find("&") > 0:
					index = address.find("&")
					street1 = address[0:index]
					street2 = address[index+1:]
					addressSet.append(street1)
					addressSet.append(street2)

				elif address.find("BLOCK BLOCK") > 0:
					street = address[12:]
					addressSet.append(street)
				else:
					addressSet.append(address)

		  #yield addressSet		

		  for key in addressSet:
				d[key]+= 1

		  d_sorted_by_value = collections.OrderedDict(sorted(d.items(), reverse=True,key=lambda x: x[1]))
		  #yield d_sorted_by_value
		  sortedAddresses = [] 

		  for i in range(0,3):
			sortedAddresses.append(d_sorted_by_value.keys()[i])
		  
		  for crime in crimeJson["crimes"]:
			if not (crime_type.has_key(crime["type"])):
				crime_type[crime["type"]] = 0

		  for crime in crimeJson["crimes"]:
			total_count += 1
			crime_type[crime["type"]] += 1
			hours = int(crime["date"][9:11])
			mins = int(crime["date"][12:14])
			temp = crime["date"][15:]
			if (hours == 3 and mins > 0) or (hours > 3 and hours < 6) or (hours == 6 and mins == 0):
				if temp == 'AM':
					event_time["3:01am-6am"] += 1
				else:
					event_time["3:01pm-6pm"] += 1

			elif (hours == 6 and mins > 0) or (hours > 6 and hours < 9) or (hours == 9 and mins == 0):
				if temp == 'AM':
					event_time["6:01am-9am"] += 1
				else:
					event_time["6:01pm-9pm"] += 1

			elif (hours == 9 and mins > 0) or (hours > 9 and hours < 12):
				if( temp == 'AM'):
					event_time["9:01am-12noon"] += 1
				else:
					event_time["9:01pm-12midnight"] += 1

			elif (hours == 12 and mins > 0) or (hours > 0 and hours < 3) or (hours == 3 and mins == 0):
				if( temp == 'AM'):
					event_time["12:01am-3am"] += 1
				else:
					event_time["12:01pm-3pm"] += 1 

			elif hours == 12 and mins == 0:
				if( temp == 'AM'):
					event_time["9:01pm-12midnight"] += 1
				else:
					event_time["9:01am-12noon"] += 1
				#yield time
			#if crime["address"] in sortedAddresses:

			#yield crime
				
				
		  resp["total_crime"] = total_count
		  resp["the_most_dangerous_streets"] = sortedAddresses
		  resp["crime_type_count"] = crime_type
		  resp["event_time_count"] = event_time
		  yield sorted(resp.items(), reverse=True)

application = Application([HelloWorldService],
	tns='spyne.examples.hello',
	in_protocol=HttpRpc(validator='soft'),
	out_protocol=JsonDocument()
)

if __name__ == '__main__':
	# You can use any Wsgi server. Here, we chose
	# Python's built-in wsgi server but you're not
	# supposed to use it in production.
	from wsgiref.simple_server import make_server

	wsgi_app = WsgiApplication(application)
	server = make_server('0.0.0.0', 8000, wsgi_app)
	server.serve_forever()