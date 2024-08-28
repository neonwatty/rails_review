import pytest
import os
import json
import time
import uuid
import requests
import boto3
from sqs.messages.message_poll import message_poll_no_id
from sqs.messages.message_delete import message_delete
from tests.utilities.execute_subprocess import execute_subprocess_command
from tests.utilities.receiver_utilities import step_setup, check_success, clean_up, s3sqs_event_maker
from tests.utilities.docker_utilities import print_container_logs


"""
This set of tests for the receiver_preprocess tests the following

- a successful test, including
    - upload a test file to s3 test bucket
    - excitation by lambda invoke
    - checks for transferred file in new location (test bucket as well)
    - cleanup of files in test bucket
    - various failures (based on json packaging failure, or other)
"""

# get current directory paths
current_directory = os.getcwd()
home_dir = os.path.expanduser("~")

# define docker variables
DOCKER_PORT = 9000
LAMBDA_ENDPOINT = f"http://localhost:{DOCKER_PORT}/2015-03-31/functions/function/invocations"

# Define your test parameters
APP_NAME = os.environ["APP_NAME"]
STAGE = "test"
BUCKET_TEST = f"{os.environ["APP_NAME"]}-test"
IMAGE_NAME = "receiver_start"
USER_ID = os.getenv("USER_ID_TEST_1")
TEST_QUEUE = f"{APP_NAME}-test"

# define session
aws_profile = os.getenv("AWS_PROFILE")
session = boto3.Session(profile_name=aws_profile, region_name="us-west-2")

# define clients
s3_client = session.client("s3")
lambda_client = session.client("lambda")

# test file data
test_file_name = "receiver_start"
test_file_path = "tests/test_files/blank.jpg"

@pytest.fixture(scope="module")
def container_controller():
    # build image
    command = ["bash", "build_image.sh", STAGE, IMAGE_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")

    # startup container
    command = [
        "docker",
        "run",
        "--env-file",
        "../.env",
        "-e", "STAGE=test",
        "-d",
        "-v",
        f"{home_dir}/.aws:/root/.aws",
        "--name",
        IMAGE_NAME,
        "-p",
        f"{DOCKER_PORT}:8080",
        IMAGE_NAME,
    ]

    stdout = execute_subprocess_command(command)

    # let container startup before sending post tests
    time.sleep(5)

    yield

    # stop and remove container
    command = ["docker", "stop", IMAGE_NAME]
    stdout = execute_subprocess_command(command)

    command = ["docker", "rm", IMAGE_NAME]
    stdout = execute_subprocess_command(command)


def test_success(container_controller, subtests):
    # construct event payload for app
    upload_id = 0
    user_id = 0
    s3_key = "0"*10
    payload = {
      "message": 'File uploaded successfully',
      "upload_id": upload_id,
      "user_id": user_id,
      "file_key": s3_key,
      "bucket_name": BUCKET_TEST,
      "stage": "test"
    }
  
    # upload test file - first create s3_key
    s3_key_save =  f"{user_id}/{upload_id}/receiver_start"

    with subtests.test(msg="create a test file"):
        with open(test_file_path, "rb") as file_data:
            s3_client.put_object(Bucket=BUCKET_TEST, Key=s3_key, Body=file_data)
    
    # execute lambda in local docker container
    with subtests.test(msg="execute docker lambda locally"):
        # Send a POST request to the Lambda function
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(payload), headers={"Content-Type": "application/json"})

        # print docker logs
        print_container_logs(IMAGE_NAME)
        
        # check response successful, and tables / files look as they should given success
        assert response.status_code == 200
        if s3_key_save is not None:
            body = json.loads(response.json()["body"])        
            assert "s3_key_save" in list(body.keys()), "FAILURE: return value s3_key_save from execution not present"
            assert "bucket_name_save" in list(body.keys()), "FAILURE: return value bucket_name_save from execution not present"
            s3_key_save = body["s3_key_save"]
            bucket_name_save = body["bucket_name_save"]
        content = json.loads(response.content.decode('utf-8'))
        assert content["statusCode"] == 200
        
        # check for message in test queue
        receipt_handle = None
        with subtests.test(msg="check message queue"):
            # poll queue
            queue_data = message_poll_no_id(TEST_QUEUE)
            
            # unpack queue data
            message_id = queue_data["message_id"]
            message = queue_data["message"]
            receipt_handle = queue_data["receipt_handle"]
            
            # unpack message
            assert message["url"] == "status_update"
            assert message["lambda"] == "receiver_start"
            assert message["status"] == "complete"
            
        # delete message
        with subtests.test(msg="delete message"):
            delete_response = message_delete(TEST_QUEUE, receipt_handle)
            assert delete_response is True
       
        # check output file exists
        with subtests.test(msg="check that output file now exists"):
            s3_client.head_object(Bucket=bucket_name_save, Key=s3_key_save)
            
        # delete input test file
        with subtests.test(msg="delete test file"):
            response = s3_client.delete_object(Bucket=BUCKET_TEST, Key=s3_key)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 204, f"FAILURE: deletion failed {BUCKET_TEST}/{s3_key}"

        # delete output test file
        with subtests.test(msg="delete test output file"):
            response = s3_client.delete_object(Bucket=BUCKET_TEST, Key=s3_key_save)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 204, f"FAILURE: deletion failed {BUCKET_TEST}/{s3_key}"