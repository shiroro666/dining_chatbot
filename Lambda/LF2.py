import boto3
import json
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import requests

def lambda_handler(event, context):
    # TODO implement
    message = json.loads(event["Records"][0]["body"])
    location = message["location"]
    cuisine = message["cuisine"].capitalize()
    date = message["date"]
    time = message["time"]
    number = message["number"]
    phone = str(message["phone"])
    
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session(aws_access_key_id = "", aws_secret_access_key = '').get_credentials()
    #credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    host = 'search-restaurants-zkjo4giy3pmt6lcyuj3s6xmumi.us-east-1.es.amazonaws.com'
    
    es = Elasticsearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection)
    result = es.search(index="restaurant", doc_type="_doc", body={"query": {"function_score": {"query" : {"match": {"cuisine":cuisine}},"random_score": {}}}}, size=3)
    
    #print(result)
    restaurant_id_list = []
    for res in result['hits']['hits']:
        restaurant_id_list.append(res['_id'])
    print(restaurant_id_list)
    db = boto3.resource('dynamodb')
    table = db.Table('yelp-restaurants')
    restaurant_info_list = []
    for bid in restaurant_id_list:
        restaurant_info_list.append(table.get_item(Key={'business_id': bid}))
    #print(restaurant_info_list)
    

    # Send a SMS message to the specified phone number
    if len(phone) == 10:
        phone = "+1" + phone
    if len(phone) == 11:
        phone = "+" + phone
    content ="Hello! Here are my " + cuisine + " restaurant suggestions for " + number + " people, for " + date + " " + time+": "
    for i in range(3):
        r = restaurant_info_list[i]["Item"]["name"] + ", located at " + restaurant_info_list[i]["Item"]["address"]+"; "
        content += str(i+1) +"." + r
    content += "Enjoy your meal!"
    print(content)
    sns = boto3.client('sns')
    if len(phone) == 12 and phone[0] == "+":
        print("message sent")
        sns.publish(MessageStructure='string', PhoneNumber=phone, Message=content)


    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
