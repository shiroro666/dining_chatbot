import json
import datetime
import time
import os
import dateutil.parser
import logging
import math
import boto3
import logging

#log = logging.getLogger()
#log.setLevel(logging.DEBUG)

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }
    
def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')
    
def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None
        

        
def isvalid_city(location):
    #valid_cities = ['new york', 'los angeles', 'chicago', 'seattle', 'madison']
    valid_cities = ['manhattan']
    return location.lower() in valid_cities
    
def isvalid_cuisine(cuisine):
    valid_cuisine = ['chinese', 'japanese', 'american', 'italian', 'indian']
    return cuisine.lower() in valid_cuisine
    
def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False
        
def isvalid_time(time):
    if len(time) != 5:
        return False
    hour, minute = time.split(':')
    hour = parse_int(hour)
    minute = parse_int(minute)
    if math.isnan(hour) or math.isnan(minute):
        return False
    return True
    #if hour < 10 or hour > 16:
    #    return build_validation_result(False, 'PickupTime', 'Our business hours are from ten a m. to five p m. Can you specify a time during this range?')

def isvalid_number(number):
    num = parse_int(number)
    if num == float('nan'):
        return False
    return True
    
def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }
    
def validate_dining(slots):
    location = try_ex(lambda: slots['Location'])
    cuisine = try_ex(lambda: slots['Cuisine'])
    date = try_ex(lambda: slots['Date'])
    time = try_ex(lambda: slots['Time'])
    number = safe_int(try_ex(lambda: slots['NumberofPeople']))
    phone = try_ex(lambda: slots['Time'])

    if location is not None and not isvalid_city(location):
        return build_validation_result(
            False,
            'Location',
            'We currently do not support {} as a valid destination. We are now only providing dining suggestion for Manhattan.'.format(location)
        )
        
    if cuisine is not None and not isvalid_cuisine(cuisine):
        return build_validation_result(
            False,
            'Cuisine',
            'We currently do not support searching for {} cuisine.  Can you try a different cuisine? The available options are: Chinese, Japanese, American, Italian, Indian.'.format(cuisine)
        )
        
    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date', 'I did not understand your dining date. What day would you like to have a meal?')
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'Date', 'You cannot get dining suggestions for the day before today. Can you try a different date?')
        
    if time is not None :
        if not isvalid_time(time):
            return build_validation_result(False, 'Time', 'Please provide a valid time')
        else:
            hour, minute = time.split(':')
            hour = parse_int(hour)
            minute = parse_int(minute)
            now = datetime.datetime.now()
            now_hour = now.hour
            now_minute = now.minute
            if datetime.datetime.strptime(date, '%Y-%m-%d').date() == datetime.date.today():
                if hour <= now_hour:
                    if hour < now_hour:
                        return build_validation_result(False, 'Time', 'You cannot choose a time before or at the current time. Please enter your time again!')
                    elif minute <= now_minute:
                        return build_validation_result(False, 'Time', 'You cannot choose a time before or at the current time. Please enter your time again!')

            if hour < 10 or hour > 20:
                return build_validation_result(False, 'Time', 'We recommend you to dine between 10 a m. to 9 p m. Can you specify a time during this range?')

    if number is not None :
        if not isvalid_number(number):
            return build_validation_result(False, 'NumberofPeople', 'Please provide a valid number')
        else:
            num = parse_int(number)
            if num > 20 or num < 1:
                return build_validation_result(False, 'NumberofPeople', 'Sorry, we only support dining suggestion for group with size between 1 and 20.')

    return build_validation_result(True, None, None)

def greeting(intent_request):
    slots = intent_request['currentIntent']['slots']
    response = {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": "Hi there! I am your Dining Concierge Virtual Assistant, what can I do for you? We are now providing dining suggestion service!"
            }
        }
    }
    return response
    
def thank(intent_request):
    response = {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": "Thank you for trying out our service!"
            }
        }
    }
    return response
    
def book_restaurant(intent_request):
    location = try_ex(lambda: intent_request['currentIntent']['slots']['Location'])
    cuisine = try_ex(lambda: intent_request['currentIntent']['slots']['Cuisine'])
    date = try_ex(lambda: intent_request['currentIntent']['slots']['Date'])
    time = try_ex(lambda: intent_request['currentIntent']['slots']['Time'])
    number = try_ex(lambda: intent_request['currentIntent']['slots']['NumberofPeople'])
    phone = safe_int(try_ex(lambda: intent_request['currentIntent']['slots']['Phone']))
    
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    # Load confirmation history and track the current reservation.
    reservation = json.dumps({
        'Location': location,
        'Cuisine': cuisine,
        'Date': date,
        'Time': time,
        'Number': number,
        'Phone': phone
    })
    
    session_attributes['currentReservation'] = reservation
    
    if intent_request['invocationSource'] == 'DialogCodeHook':
        
        validation_result = validate_dining(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots = intent_request['currentIntent']['slots']
            slots[validation_result['violatedSlot']] = None

            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        session_attributes['currentReservation'] = reservation
        return delegate(session_attributes, intent_request['currentIntent']['slots'])

    #logger.debug('bookHotel under={}'.format(reservation))
    session_attributes['lastConfirmedReservation'] = reservation
    
    # Get the service resource
    sqs = boto3.resource('sqs', 'us-east-1')

    # Get the queue
    queue = sqs.get_queue_by_name(QueueName='chatbotQueue')

    # Create a new message
    message = json.dumps({
        "location": str(location),
        "cuisine": str(cuisine),
        "date": str(date),
        "time": str(time),
        "number": str(number),
        "phone": str(phone)
    })
    message = message.replace("\'", "\"")
    print(message)
    queue.send_message(MessageBody=message)
    
    # The response is NOT a resource, but gives you a message ID and MD5
    #log.debug(res.get('MessageId'))

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, I am now searching for appropriate restaurant for you. I will send you a message after I find something.'
        }
    )

def dispatch(intent_request):
    intent_name = intent_request['currentIntent']['name']
    if intent_name == "GreetingIntent":
        return greeting(intent_request)
    elif intent_name == "ThankYouIntent":
        return thank(intent_request)
    elif intent_name == "DiningSuggestionsIntent":
        return book_restaurant(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')
        
def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    return dispatch(event)
    