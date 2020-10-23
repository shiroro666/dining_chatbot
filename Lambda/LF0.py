import json
import boto3
def lambda_handler(event, context):
    text = "test"
    #print(event)
    text = json.loads(event['body'])['messages'][0]["unstructured"]["text"]
    #test2 = event['message']
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='DiningService', 
        botAlias='BETA', 
        userId='user', 
        sessionAttributes={},
        requestAttributes={},
        inputText=text)
    #print(response['message'])
    return {
        'headers':{
            'Access-Control-Allow-Origin': '*'
        },
        'statusCode': 200,
        'body': json.dumps({"messages": [
            {
                "type": "unstructured",
                "unstructured": {
                    "id": "string",
                    "text": response['message'],
                    "timestamp": "string"
                }
            }
        ]})
    }
