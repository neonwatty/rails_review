import os
import json
import functools
from sqs.messages.message_create import message_create
from sqs.messages.message_delete import message_delete

STAGE = os.environ["STAGE"]
APP_NAME = os.environ["APP_NAME"]
STATUS_QUEUE = f"{APP_NAME}-test-status"
if STAGE in ["development", "production"]:
    STATUS_QUEUE = f"{APP_NAME}-status"
    BUCKET_NAME_SAVE = f"{APP_NAME}-trigger"
    

def sqs_status_wrapper(func):
    @functools.wraps(func)
    def wrapper(event, context):
        # unpack setup_payload from event
        setup_payload = event["setup_payload"]
        
        # run func
        result = func(event, context)
        
        # check result code
        if result["statusCode"] == 200:
            # send complete status signal to queue
            status = {
                "url": "status_update",
                "lambda": "receiver_preprocess",
                "user_id": setup_payload["user_id"],
                "upload_id": setup_payload["upload_id"],
                "status": "complete"
            }
            
            # send message to queue
            response = message_create(STATUS_QUEUE, status)
            
            # check status response
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                success_message = "SUCCESS: receiver_start executed successfully"
                return {
                    'statusCode': 200,
                    'body': json.dumps({'status': 'success', 'message': success_message, "s3_key_save":result["s3_key_save"], "bucket_name_save": result["bucket_name_save"]})
                }
            else:
                failure_message = f"FAILURE: status message for {setup_payload["RECEIVER_NAME"]} failed to send"
                return {
                    'statusCode': 500,
                    'body': json.dumps({'status': 'success', 'message': failure_message, "s3_key_save":None, "bucket_name_save": None})
                }
        else:
            # send status update to queue   
            status = {
                "url": "status_update",
                "lambda": "receiver_preprocess",
                "user_id": setup_payload["user_id"],
                "upload_id": setup_payload["upload_id"],
                "status": "fail"
            }
            response = message_create(STATUS_QUEUE, status)
            
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                success_message = "SUCCESS: receiver_start executed successfully"
                return {
                    'statusCode': 200,
                    'body': json.dumps({'status': 'success', 'message': success_message, "s3_key_save":result["s3_key_save"], "bucket_name_save": result["bucket_name_save"]})
                }
            else:
                failure_message = f"FAILURE: status message for {setup_payload["RECEIVER_NAME"]} failed to send"
                return {
                    'statusCode': 500,
                    'body': json.dumps({'status': 'success', 'message': failure_message, "s3_key_save":None, "bucket_name_save": None})
                }


def sqs_receiver_wrapper(func):
    @functools.wraps(func)
    def wrapper(event, context):
        try:
            # Unpack records
            if "Records" not in event:
                raise KeyError("No 'records' found in the event")
            records = event.get("Records", [])
            general_record = records[0]
            
            if "eventSourceARN" not in general_record:
                raise KeyError("No 'eventSourceARN' found in general_record")
            queue_arn = general_record["eventSourceARN"]
            
            if "receiptHandle" not in general_record:
                raise KeyError("No 'receiptHandle' found in general_record")
            receipt_handle = general_record["receiptHandle"]

            queue_name = queue_arn.split(":")[-1]
            s3_record = json.loads(general_record["body"])["Records"][0]            

            # Process message
            process_response = func(s3_record, {})

            # check status of response
            if process_response["statusCode"] > 200:
                return process_response

            if not queue_name:
                raise ValueError("Next queue name not found in response body")

            # Delete message
            del_message_val = message_delete(queue_name, receipt_handle)

            # Return if processing or deletion failed
            if not del_message_val:
                return {
                    "statusCode": 400,
                    "body": json.dumps("BAD REQUEST: Error processing SQS message"),
                }

            return process_response

        except Exception as e:
            failure_message = f"BAD REQUEST: Error processing SQS message: {e}"
            print(failure_message)
            return {
                "statusCode": 500,
                "body": json.dumps(failure_message),
            }

    return wrapper
