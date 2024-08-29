import os
import json
import requests
from decorators.warmer import warmer
from decorators.receiver import receiver_decorator


RAILS_DEVELOPMENT_HOST = os.environ["RAILS_DEVELOPMENT_HOST"]
LAMBDA_API_KEY = os.getenv('LAMBDA_API_KEY')

@warmer
@receiver_decorator(local_input_ext=".jpg", local_output_ext="")
def lambda_handler(event, context):    
    try:        
        # setup payload        
        message = event["message"]
        url = message["url"]
        del message["url"]

        # create headers
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LAMBDA_API_KEY}'
        }

        # create url
        rails_url = f"{RAILS_DEVELOPMENT_HOST}/lambda_status/{url}"
        
        # fire off request
        response = requests.post(rails_url, data=json.dumps(message), headers=headers)
                
        # return 
        message = f"SUCCESS: receiver for {event["receiver_name"]} ran successfully"
        print(message)
        return {
            "statusCode": 200,  "body": {"receiver_name": event["receiver_name"], "message": message}
        }
    except Exception as e:
        message = f"FAILURE: receiver for {event["receiver_name"]} failed with exception {str(e)}"
        print(message)
        return {"statusCode": 500, "body": {"receiver_name": event["receiver_name"], "message": message}}