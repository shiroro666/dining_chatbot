import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
import requests
from requests_aws4auth import AWS4Auth

cuisine = ['Chinese', 'Japanese', 'American', 'Italian', 'Indian']
credentials = boto3.Session(aws_access_key_id = "", aws_secret_access_key = '').get_credentials()

region = 'us-east-1' # e.g. us-east-1
service = 'es'
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = 'search-restaurants-zkjo4giy3pmt6lcyuj3s6xmumi.us-east-1.es.amazonaws.com' # the Amazon ES domain, with https://
#index = 'lambda-index'
#type = 'lambda-type'
#url = host + '/' + index + '/' + type + '/'

es = Elasticsearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection)

#f = open("restaurant-5.json")
#restaurants = json.load(f)
#for d in restaurants["yelp-restaurants"]:
#    temp = d["PutRequest"]["Item"]
#    document = {"business_id": temp["business_id"]["S"],"cuisine": temp["category"]["S"]}
#    es.index(index = "restaurant", doc_type = "_doc", id = document["business_id"], body = document)

condition = {"query": {"function_score": {"query" : {"match": {"cuisine":"Chinese"}},"random_score": {}}}}
#condition = {"query": {"match": {"cuisine":"Chinese"}}}
result = es.search(index="restaurant", doc_type="_doc", body=condition, size=5)
print(result)

