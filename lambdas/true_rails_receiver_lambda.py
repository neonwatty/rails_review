import json

def lambda_handler(event, context):
    # The 'event' parameter contains the payload sent to the Lambda function
    try:
        print(f"event {event}")
        print(f"type of event {type(event)}")
        
        
        # Parse the JSON payload
        message = event["message"]
        file_key = event["file_key"]
        
        print("extracted data from event")
        
        print(f"message --> {message}")
        print(f"file_key --> {file_key}")
        
        
        # Process the file_key as needed
        # For example, you might want to fetch the file from S3 or perform other actions
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'success', 'message': message})
        }
        
    except json.JSONDecodeError:
        # Handle JSON decode errors
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Invalid JSON payload'})
        }
    except Exception as e:
        # Handle other potential errors
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }