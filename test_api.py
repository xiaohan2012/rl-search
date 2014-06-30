import sys
import json, urllib2, redis
from pprint import pprint

# redis = redis.StrictRedis(host="ugluk", port=6379, db='test')
# redis.flushdb()

url = 'http://127.0.0.1/api/1.0/recommend'
req = urllib2.Request(url)

req.add_header('Content-Type', 'application/json')

query = 'python database'
print "Query:", query
response = urllib2.urlopen(req, json.dumps({
    'query': query
}))
res = json.loads(response.read())
session_id = res['session_id']

print 'Initialization session id.'
pprint(res)

print 'First round:'

req = urllib2.Request(url)
req.add_header('Content-Type', 'application/json')

response = urllib2.urlopen(req, json.dumps({
    'session_id': session_id,
    'doc_fb': [{'id':5, 'score': 0.1}, {'id': 6, 'score': 0.8}],
    'kw_fb': [{'id': 'key-value-storage', 'score': 0.8}, {'id': 'database', 'score': 0.6}]
}))

res = json.loads(response.read())
pprint(res)

print 'Second round..'
req = urllib2.Request(url)
req.add_header('Content-Type', 'application/json')

response = urllib2.urlopen(req, json.dumps({
    'session_id': session_id,
    'doc_fb': [{'id':1, 'score': 0.8}, {'id': 2, 'score': 0.8}],
    'kw_fb': [{'id': 'redis', 'score': 0.8}, {'id': 'database', 'score': 0.8}]
}))

res = json.loads(response.read())
pprint(res)
    
sys.exit(-1)
