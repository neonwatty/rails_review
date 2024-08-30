import os
import boto3
import json
import uuid
import time
from sqs.messages.message_create import message_create
from sqs.messages.message_poll import message_poll


# define session
aws_profile = os.getenv("AWS_PROFILE")
session = boto3.Session(profile_name=aws_profile, region_name="us-west-2")

# define clients
s3_client = session.client("s3")
lambda_client = session.client("lambda")

# import variables
APP_NAME = os.environ["APP_NAME"]
STAGE = "test"
BUCKET_TEST = f"{os.environ["APP_NAME"]}-test"
IMAGE_NAME = "receiver_preprocess"
LAMBDA_FUNCTION_NAME = f"receivers-{STAGE}-{IMAGE_NAME}"
SQS_ARN_ROOT = os.environ["SQS_ARN_ROOT"]
TEST_RECEIVERS_QUEUE = f"{APP_NAME}-test-receivers"

# create event - nested like triggered event from s3 --> sqs
def s3sqs_event_maker(bucket_name: str, s3_key: str, queue_name: str, receipt_handle: str) -> dict:
        ## build record for triggering receiver
        # build s3 record
        bucket = {}
        bucket["name"] = bucket_name
        object = {}
        object["key"] = s3_key
        s3 = {}
        s3["bucket"] = bucket
        s3["object"] = object
        s3_record = {"s3": s3}
        
        # build queue record
        queue_arn = f"{SQS_ARN_ROOT}{queue_name}"

        # construct general record
        general_record = {
            "eventSourceARN": queue_arn,
            "receiptHandle": receipt_handle,
            "body": json.dumps({
                "Records": [s3_record]
            })
        }
        
        # construct general records holder
        event = {
            "Records": [general_record]
        }
        
        # construct event
        return event


def step_setup(subtests, test_file_name, test_file_path, step: str,  step_progress: str = "in_progress", file_id_override: str | None = None):
    # upload file file data for testing
    local_file_path = test_file_path
    upload_id = 0 # hash_file(test_file_path)
    request_id = str(uuid.uuid4())
    filename = test_file_name
    user_id = 0
    s3_key = f"{user_id}/{upload_id}/{filename}"
    
    # define s3_key_save based on filename
    s3_key_save = None
    if filename == "receiver_start":
        s3_key_save = f"{user_id}/{upload_id}/receiver_preprocess"
    if filename == "receiver_preprocess":
        s3_key_save = f"{user_id}/{upload_id}/receiver_process"
    
    # set status
    assert step in ["receiver_preprocess", "receiver_process", "receiver_end"]

    # upload test file
    with subtests.test(msg="create a test file"):
        with open(local_file_path, "rb") as file_data:
            s3_client.put_object(Bucket=BUCKET_TEST, Key=s3_key, Body=file_data)

    # create message in queue, poll for receipt to pass
    message_id = None
    receipt_handle = None

    ### upload first time --> for successful completion ###
    # create message
    with subtests.test(msg="create test message"):
        response = message_create(TEST_RECEIVERS_QUEUE, {})
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        message_id = response["MessageId"]

    # poll for message to get receipt
    with subtests.test(msg="poll for test message receipt"):
        receipt_handle = message_poll(TEST_RECEIVERS_QUEUE, message_id)
        assert receipt_handle is not None

    # sleep to let setup complete
    time.sleep(2)
    return upload_id, request_id, s3_key, s3_key_save, receipt_handle


def status_setup(subtests, TEST_STATUS_QUEUE):
    ### upload first time --> for successful completion ###
    # create message
    with subtests.test(msg="create test message"):
        response = message_create(TEST_STATUS_QUEUE, {})
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        message_id = response["MessageId"]

    # poll for message to get receipt
    with subtests.test(msg="poll for test message receipt"):
        receipt_handle = message_poll(TEST_STATUS_QUEUE, message_id)
        assert receipt_handle is not None
    
    # build status
    test_status = {
        "lambda": "receiver_start",
        "user_id": 0,
        "upload_id": 0,
        "status": "complete"
        }
    
    # build queue record
    queue_arn = f"{SQS_ARN_ROOT}{TEST_STATUS_QUEUE}"
    
    # construct general record
    general_record = {
        "eventSourceARN": queue_arn,
        "receiptHandle": receipt_handle,
        "body": json.dumps(test_status)
    }
        
    # construct general records holder
    event = {
        "Records": [general_record]
    }
    return event, receipt_handle