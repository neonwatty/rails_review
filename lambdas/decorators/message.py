import json
import functools
from sqs.messages.message_delete import message_delete


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
