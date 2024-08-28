import boto3
import os
import json
import pytest
from tables.public.row_read import read
from tables.public.row_update import update
from tables.public.row_destroy import destroy
from tests.utilities.execute_subprocess import execute_subprocess_command
from tests.utilities.receiver_utilities import step_setup, check_success, clean_up, s3sqs_event_maker


"""
This set of tests for the receiver_preprocess tests the following

- a successful test, including
    - excitation by sqs message
    - checks against s3 bucket upload location for original upload, file ledger, and history ledger
    - check against s3 bucket for preprocess output (here an json)
- these excitaions and checks are also performed in the following failure tests
    - a failure test, wherein the same file is (attempted) processed twice after successfully completing the first time
    - a failure test, wherein the same file is (attempted) processed twice after first in progress

    - a failure test, wherein the same file is (attempted) processed twice, after failing the first time 
    - a failure test, wherein a file's has from uploaded file does not match what the client provided
"""

# assign current directory
current_directory = os.getcwd()
home_dir = os.path.expanduser("~")

# define session
aws_profile = os.getenv("AWS_PROFILE")
session = boto3.Session(profile_name=aws_profile, region_name="us-west-2")

# define clients
s3_client = session.client("s3")
lambda_client = session.client("lambda")

# Define your test parameters
APP_NAME=os.environ["APP_NAME"]
USER_ID = os.getenv("USER_ID_TEST_1")
STAGE = os.environ.get("STAGE", "development")
BUCKET_TEST = os.environ["BUCKET_TEST"]
IMAGE_NAME = "receiver_step_1"
LAMBDA_FUNCTION_NAME = f"receivers-{STAGE}-{IMAGE_NAME}"
QUEUE_TEST = os.environ["QUEUE_TEST"]
FILE_LEDGER_TEMP = os.environ["FILE_LEDGER_TEMP"]
SERVERLESS_NAME = "serverless_receivers.yml"
HISTORY_LEDGER_MAIN = os.environ["HISTORY_LEDGER_MAIN"]

# test file data
test_file_name = "receiver_preprocess.mp3"
test_file_path = "tests/test_files/test_file.mp3"


@pytest.fixture(scope="module")
def build_deploy():
    # build image
    command = ["bash", "build_image.sh", STAGE, IMAGE_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")

    # deploy image
    command = ["bash", "deploy_image.sh", APP_NAME, STAGE, IMAGE_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")

    # deploy lambdas
    command = ["bash", "adjust_functions.sh", "deploy", STAGE, SERVERLESS_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas")


def test_success(build_deploy, subtests):
    ### setup step ###
    file_id, request_id, s3_key, s3_key_save, receipt_handle = step_setup(subtests, test_file_name, test_file_path, IMAGE_NAME, step_progress="not started")
    event = s3sqs_event_maker(BUCKET_TEST, s3_key, QUEUE_TEST, receipt_handle)

    # execute lambda in local docker container
    with subtests.test(msg="execute docker lambda locally"):
        # Send a POST request to the Lambda function
        response = lambda_client.invoke(FunctionName=LAMBDA_FUNCTION_NAME, InvocationType="RequestResponse", Payload=json.dumps(event))

        # check response successful, and tables / files look as they should given success
        check_success(subtests, response, file_id, s3_key_save, local=False)

    # clean up
    clean_up(subtests, s3_key, s3_key_save, file_id)


def test_fail_file_already_preprocess_successfully(build_deploy, subtests):
    ### first upload - succeeds ###
    # setup step
    file_id, request_id, s3_key, s3_key_save, receipt_handle = step_setup(subtests, test_file_name, test_file_path, IMAGE_NAME, step_progress="not started")
    event = s3sqs_event_maker(BUCKET_TEST, s3_key, QUEUE_TEST, receipt_handle)

    # execute lambda in local docker container
    with subtests.test(msg="execute docker lambda locally"):
        # Send a POST request to the Lambda function
        response = lambda_client.invoke(FunctionName=LAMBDA_FUNCTION_NAME, InvocationType="RequestResponse", Payload=json.dumps(event))

        # check response successful, and tables / files look as they should given success
        check_success(subtests, response, file_id, s3_key_save, local=False)

    ### upload second time - rejection due to prior completion ###
    # execute lambda in local docker container
    with subtests.test(msg="execute docker lambda locally"):
        # Send a POST request to the Lambda function
        response = lambda_client.invoke(FunctionName=LAMBDA_FUNCTION_NAME, InvocationType="RequestResponse", Payload=json.dumps(event))

        # Check the response
        assert response["StatusCode"] == 200
        streaming_body = response["Payload"]
        content = json.loads(streaming_body.read().decode("utf-8"))
        assert content["statusCode"] == 400
        body = json.loads(content["body"])
        message = body["message"]
        assert "file with file_id already exist" in message

    ### clean up files and tables ###
    clean_up(subtests, s3_key, s3_key_save, file_id)


def test_file_preprocess_in_progress(build_deploy, subtests):
    # setup step
    file_id, request_id, s3_key, s3_key_save, receipt_handle = step_setup(subtests, test_file_name, test_file_path, IMAGE_NAME, step_progress="in progress")
    event = s3sqs_event_maker(BUCKET_TEST, s3_key, QUEUE_TEST, receipt_handle)

    # replace status "complete" with "in progress"
    read_response = read(FILE_LEDGER_TEMP, "file_id", file_id)
    read_status = read_response[0].get("status", None)
    read_status["receiver_preprocess"] = "in progress"
    update_document = {"status": read_status}
    update(FILE_LEDGER_TEMP, "file_id", file_id, update_document)

    # execute lambda in local docker container
    with subtests.test(msg="execute docker lambda locally"):
        # Send a POST request to the Lambda function
        response = lambda_client.invoke(FunctionName=LAMBDA_FUNCTION_NAME, InvocationType="RequestResponse", Payload=json.dumps(event))

        # Check the response
        assert response["StatusCode"] == 200
        streaming_body = response["Payload"]
        content = json.loads(streaming_body.read().decode("utf-8"))
        assert content["statusCode"] == 400
        body = json.loads(content["body"])
        message = body["message"]
        assert "file with file_id already exist" in message

    ### clean up files and tables ###
    clean_up(subtests, s3_key, s3_key_save, file_id)


def test_failure_previous_fail(build_deploy, subtests):
    ### setup step ###
    file_id, request_id, s3_key, s3_key_save, receipt_handle = step_setup(subtests, test_file_name, test_file_path, IMAGE_NAME, step_progress="fail")
    event = s3sqs_event_maker(BUCKET_TEST, s3_key, QUEUE_TEST, receipt_handle)

    # execute lambda locally
    with subtests.test(msg="execute handler"):
        # Send a POST request to the Lambda function
        response = lambda_client.invoke(FunctionName=LAMBDA_FUNCTION_NAME, InvocationType="RequestResponse", Payload=json.dumps(event))

        # Check the response
        assert response["StatusCode"] == 200
        streaming_body = response["Payload"]
        content = json.loads(streaming_body.read().decode("utf-8"))
        assert content["statusCode"] == 400
        body = json.loads(content["body"])
        message = body["message"]
        assert "file with file_id failed recently" in message

    # check that row in history-ledger table does not exist
    with subtests.test(msg="check that row for file_id not in history ledger"):
        response = read(HISTORY_LEDGER_MAIN, "file_id", file_id)
        assert len(response) > 0

    ### clean up ###
    clean_up(subtests, s3_key, s3_key_save, file_id)


def test_failure_hash_mismash(build_deploy, subtests):
    ### setup step ###
    file_id_mismatch = "this is not the same hash as above"
    file_id, request_id, s3_key, s3_key_save, receipt_handle = step_setup(subtests, test_file_name, test_file_path, IMAGE_NAME, step_progress="not started", file_id_override=file_id_mismatch)
    event = s3sqs_event_maker(BUCKET_TEST, s3_key, QUEUE_TEST, receipt_handle)

    # execute lambda locally
    with subtests.test(msg="execute handler"):
        # Send a POST request to the Lambda function
        response = lambda_client.invoke(FunctionName=LAMBDA_FUNCTION_NAME, InvocationType="RequestResponse", Payload=json.dumps(event))

        # Check the response
        assert response["StatusCode"] == 200
        streaming_body = response["Payload"]
        content = json.loads(streaming_body.read().decode("utf-8"))
        assert content["statusCode"] == 400
        body = json.loads(content["body"])
        message = body["message"]
        assert "failed due to no row in temp file ledger" in message

    # check that row in history-ledger table does not exist
    with subtests.test(msg="check that row for file_id not in history ledger"):
        response = read(HISTORY_LEDGER_MAIN, "file_id", file_id_mismatch)
        assert len(response) == 0

    # check that row in history-ledger table does exist
    with subtests.test(msg="check that row for file_id not in history ledger"):
        response = read(HISTORY_LEDGER_MAIN, "file_id", file_id)
        assert len(response) > 0

    # delete row from file-ledger table associated with file_id
    with subtests.test(msg="delete row in table for file_id "):
        response = destroy(FILE_LEDGER_TEMP, "file_id", file_id_mismatch)
        assert response is True, f"FAILURE: failed to delete row in file-ledger table with file_id {file_id}"

    ### clean up ###
    clean_up(subtests, s3_key, s3_key_save, file_id)
