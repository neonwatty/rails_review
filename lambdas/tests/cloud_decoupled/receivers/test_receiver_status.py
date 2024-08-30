import pytest
import os
import json
import boto3
from sqs.messages.message_poll import message_poll_no_id
from sqs.messages.message_delete import message_delete
from tests.utilities.execute_subprocess import execute_subprocess_command
from tests.utilities.receiver_utilities import status_setup
from config import APP_NAME, STAGE

# get current directory paths
current_directory = os.getcwd()
home_dir = os.path.expanduser("~")

# Define your test parameters
BUCKET_TEST = f"{APP_NAME}-{STAGE}"
TEST_STATUS_QUEUE = f"{APP_NAME}-status-{STAGE}"
TEST_RECEIVERS_QUEUE = f"{APP_NAME}-receivers-{STAGE}"
RECEIVER_NAME = "receiver_status"
RAILS_DEVELOPMENT_HOST = os.environ["RAILS_DEVELOPMENT_HOST"]
LAMBDA_API_KEY = os.environ["LAMBDA_API_KEY"]
SQS_ARN_ROOT = os.environ["SQS_ARN_ROOT"]
SERVERLESS_NAME = "serverless_receivers.yml"
LAMBDA_FUNCTION_NAME = f"{APP_NAME}-{RECEIVER_NAME}-{STAGE}"

# define session
aws_profile = os.getenv("AWS_PROFILE")
session = boto3.Session(profile_name=aws_profile, region_name="us-west-2")

# define clients
s3_client = session.client("s3")
lambda_client = session.client("lambda")

# test file data
test_file_name = "receiver_process"
test_file_path = "tests/test_files/blank.jpg"

@pytest.fixture(scope="module")
def build_deploy():
    # build image
    print("INFO: starting image building process...")
    command = ["bash", "build_image.sh", STAGE, RECEIVER_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")
    print("INFO: ...complete!")

    # deploy image
    print("INFO: starting image deploy process...")
    command = ["bash", "deploy_image.sh", STAGE, RECEIVER_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")
    print("INFO: ...complete!")

    # deploy lambdas
    print("INFO: starting service deploy process...")
    command = ["bash", "adjust_functions.sh", "deploy", STAGE, SERVERLESS_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas")
    print("INFO: ...complete!")



def test_success(build_deploy, subtests):
    print("INFO: starting test_success")
    
    # create sqs event to trigger status receiver with
    event, status_receipt_handle = status_setup(subtests, TEST_STATUS_QUEUE)
  
    # execute function
    with subtests.test(msg="execute function"):
        # invoke lambda
        response = lambda_client.invoke(FunctionName=LAMBDA_FUNCTION_NAME, InvocationType="RequestResponse", Payload=json.dumps(event))
        
        # check response successful, and tables / files look as they should given success
        assert response["StatusCode"] == 200
        streaming_body = response["Payload"]
        content = json.loads(streaming_body.read().decode("utf-8"))
        assert content["statusCode"] == 200
        
    # delete status message
    with subtests.test(msg="delete status message"):
        delete_response = message_delete(TEST_STATUS_QUEUE, status_receipt_handle)
        assert delete_response is True
    