import os
import boto3
import json
import uuid
import time
from botocore.exceptions import ClientError
from sqs.messages.message_create import message_create
from sqs.messages.message_poll import message_poll
from tables.public.row_create import create
from tables.public.row_update import update
from tables.public.row_read import read
from tables.public.row_destroy import destroy
from s3.subdir_delete import delete_subdir
from utilities.tools.hash import hash_file


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
USER_ID = os.getenv("USER_ID_TEST_1")
SQS_ARN_ROOT = os.environ["SQS_ARN_ROOT"]
TEST_STATUS_QUEUE = f"{APP_NAME}-test-status"
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


def check_success(subtests, response, local: bool = True) -> tuple[str]:
    s3_key_save = None
    bucket_name_save = None
    if local:
        # Check the response
        assert response.status_code == 200
        if s3_key_save is not None:
            body = json.loads(response.json()["body"])        
            assert "s3_key_save" in list(body.keys()), "FAILURE: return value s3_key_save from execution not present"
            assert "bucket_name_save" in list(body.keys()), "FAILURE: return value bucket_name_save from execution not present"
            s3_key_save = body["s3_key_save"]
            bucket_name_save = body["bucket_name_save"]
        content = json.loads(response.content.decode('utf-8'))
        assert content["statusCode"] == 200
    else:
        assert response["StatusCode"] == 200
        streaming_body = response["Payload"]
        content = json.loads(streaming_body.read().decode("utf-8"))
        assert content["statusCode"] == 200
        if s3_key_save is not None:
            body = json.loads(content["body"])
            assert "s3_key_save" in list(body.keys()), "FAILURE: return values from execution not present"

    # check that processed version of test file now exists
    if s3_key_save is not None:
        with subtests.test(msg="check that output file now exists"):
            try:
                s3_client.head_object(Bucket=bucket_name_save, Key=s3_key_save)
            except ClientError as e:
                # If a ClientError is raised, the object does not exist, which is expected
                if e.response["Error"]["Code"] == "404":
                    # Object does not exist, so the deletion was successful
                    assert True, f"FAILURE: Test object does not at {bucket_name}/{s3_key_save}"
                else:
                    # Re-raise the exception if it's not a 404 error
                    raise
            else:
                # If no exception is raised, the object still exists
                assert True, f"FAILURE: Test object does not exist {bucket_name}/{s3_key_save}"
    return bucket_name_save, s3_key_save


# after work clean up
def clean_up(subtests, s3_key, s3_key_save):
    ### check / delete upload and table assets ###
    # delete test file
    if s3_key is not None:
        with subtests.test(msg="delete test file"):
            response = s3_client.delete_object(Bucket=BUCKET_TEST, Key=s3_key)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 204, f"FAILURE: deletion failed {bucket_name}/{s3_key}"

        # check that test file is deleted
        with subtests.test(msg="check that test file is deleted"):
            try:
                s3_client.head_object(Bucket=BUCKET_TEST, Key=s3_key)
            except ClientError as e:
                # If a ClientError is raised, the object does not exist, which is expected
                if e.response["Error"]["Code"] == "404":
                    # Object does not exist, so the deletion was successful
                    assert True, f"FAILURE: Test object still exists after attempted deletion at {bucket_name}/{s3_key}"
                else:
                    # Re-raise the exception if it's not a 404 error
                    raise
            else:
                # If no exception is raised, the object still exists
                assert False, f"FAILURE: Test object still exists after attempted deletion at {bucket_name}/{s3_key}"

    # delete output test file from bucket
    if s3_key_save is not None:
        with subtests.test(msg="delete test output file"):
            response = s3_client.delete_object(Bucket=BUCKET_TEST, Key=s3_key_save)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 204, f"FAILURE: deletion failed {bucket_name}/{s3_key}"

        # check that output test file from bucket has been deleted
        with subtests.test(msg="check that mp3 test file is deleted"):
            try:
                s3_client.head_object(Bucket=BUCKET_TEST, Key=s3_key_save)
            except ClientError as e:
                # If a ClientError is raised, the object does not exist, which is expected
                if e.response["Error"]["Code"] == "404":
                    # Object does not exist, so the deletion was successful
                    assert True, f"FAILURE: Test object still exists after attempted deletion at {bucket_name}/{s3_key_save}"
                else:
                    # Re-raise the exception if it's not a 404 error
                    raise
            else:
                # If no exception is raised, the object still exists
                assert False, f"FAILURE: Test object still exists after attempted deletion at {BUCKET_TEST}/{s3_key_save}"

