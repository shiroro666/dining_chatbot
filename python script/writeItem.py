import json
import boto3

def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

f = open("restaurant-5.json")
restaurants = json.load(f)

client = boto3.client("dynamodb")

for x in batch(restaurants["yelp-restaurants"], 25):
    subbatch_dict = {"yelp-restaurants": x}
    response = client.batch_write_item(RequestItems=subbatch_dict)