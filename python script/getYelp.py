import requests
import json
from datetime import datetime

API_KEY = ""
ENDPOINT = 'https://api.yelp.com/v3/businesses/search'
HEADERS = {'Authorization': 'bearer %s' % API_KEY}
cuisine = ['Chinese', 'Japanese', 'American', 'Italian', 'Indian']
#valid_cities = ['New york', 'Los Angeles', 'Chicago', 'Seattle', 'Madison, WI']
#parameters = {'term': 'Chinese', 'limit': 50, 'location': 'Manhattan'}
my_data = {"yelp-restaurants":[]}
for i in range(20):
	parameters = {'term': 'Indian', 'limit': 50, 'offset': i*50, 'location': 'Manhattan'}
	response = requests.get(url = ENDPOINT, params = parameters, headers = HEADERS)
	business_data = response.json()
	#print(type(response))
	for business in business_data['businesses']:
		record = {"PutRequest":{"Item": {}}}
		if business['id'] != "":
			record["PutRequest"]["Item"]["business_id"] = {"S":business['id']}
		record["PutRequest"]["Item"]["category"] = {"S": "Indian"}
		if business['name'] != "":
			record["PutRequest"]["Item"]["name"] = {"S": business['name']}
		if str(business['coordinates']['latitude']) != "":
			record["PutRequest"]["Item"]["latitude"] = {"S": str(business['coordinates']['latitude'])}
		if str(business['coordinates']['longitude']) != "":
			record["PutRequest"]["Item"]["longitude"] = {"S": str(business['coordinates']['longitude'])}
		if business['location']['display_address'][0] != "":
			record["PutRequest"]["Item"]["address"] = {"S": business['location']['display_address'][0]}
		if str(business['review_count']) != "":
			record["PutRequest"]["Item"]["review"] = {"N": str(business['review_count'])}
		if str(business['rating']) != "":
			record["PutRequest"]["Item"]["rating"] = {"N": str(business['rating'])}
		if str(business['location']['zip_code']) != "":
			record["PutRequest"]["Item"]["zip_code"] = {"S": str(business['location']['zip_code'])}
		record["PutRequest"]["Item"]["insertedAtTimestamp"] = {"S": str(datetime.now())}
		my_data["yelp-restaurants"].append(record)

#jstr = json.dumps(my_data)
with open("restaurant-5.json", "w") as f:
	json.dump(my_data, f, indent = 4)
f.close()

#aws dynamodb batch-write-item --request-items file://restaurant.json