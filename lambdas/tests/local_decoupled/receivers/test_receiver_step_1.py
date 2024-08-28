import pytest
import os
import json
import time
import requests
from tables.public.row_update import update
from tables.public.row_read import read
from tables.public.row_destroy import destroy
from tests.utilities.execute_subprocess import execute_subprocess_command
from tests.utilities.receiver_utilities import step_setup, check_success, clean_up, s3sqs_event_maker
from tests.utilities.docker_utilities import print_container_logs

"""
This set of tests for the receiver_preprocess tests the following

- a successful test, including
    - excitation by sqs message
    - checks against s3 bucket upload location for original upload, file ledger, and history ledger
    - check against s3 bucket for preprocess output (here a txt)
- these excitaions and checks are also performed in the following failure tests
    - a failure test, wherein the same file is (attempted) processed twice after successfully completing the first time
    - a failure test, wherein the same file is (attempted) processed twice after first in progress

    - a failure test, wherein the same file is (attempted) processed twice, after failing the first time 
    - a failure test, wherein a file's has from uploaded file does not match what the client provided
"""

# get current directory paths
current_directory = os.getcwd()
home_dir = os.path.expanduser("~")

# define docker variables
DOCKER_PORT = 9000
LAMBDA_ENDPOINT = f"http://localhost:{DOCKER_PORT}/2015-03-31/functions/function/invocations"

# Define your test parameters
STAGE = os.environ.get("STAGE", "development")
BUCKET_TEST = os.environ["BUCKET_TEST"]
IMAGE_NAME = "receiver_step_1"
LAMBDA_FUNCTION_NAME = f"receivers-{STAGE}-{IMAGE_NAME}"
QUEUE_TEST = f"{os.environ["APP_NAME"]}-test"
USER_ID = os.getenv("USER_ID_TEST_1")
FILE_LEDGER_TEMP = os.environ["FILE_LEDGER_TEMP"]
HISTORY_LEDGER_MAIN = os.environ["HISTORY_LEDGER_MAIN"]
SQS_ARN_ROOT = os.environ["SQS_ARN_ROOT"]

# test file data
test_file_name = "receiver_preprocess.mp3"
test_file_path = "tests/test_files/test_file.mp3"

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
        ".env",
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
    time.sleep(3)

    yield

    # stop and remove container
    command = ["docker", "stop", IMAGE_NAME]
    stdout = execute_subprocess_command(command)

    command = ["docker", "rm", IMAGE_NAME]
    stdout = execute_subprocess_command(command)


def test_success(container_controller, subtests):
    ### setup step ###
    file_id, request_id, s3_key, s3_key_save, receipt_handle = step_setup(subtests, test_file_name, test_file_path, IMAGE_NAME, step_progress="not started")  
    event = s3sqs_event_maker(BUCKET_TEST, s3_key, QUEUE_TEST, receipt_handle)
    
    # execute lambda in local docker container
    with subtests.test(msg="execute docker lambda locally"):
        # Send a POST request to the Lambda function
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})
        
        # print container logs
        print_container_logs(IMAGE_NAME)

        # check response successful, and tables / files look as they should given success
        check_success(subtests, response, file_id, s3_key_save)

    ### clean up files and tables ###
    clean_up(subtests, s3_key, s3_key_save, file_id)


def test_fail_file_already_preprocess_successfully(container_controller, subtests):
    ### first upload - succeeds ###
    # setup step
    file_id, request_id, s3_key, s3_key_save, receipt_handle = step_setup(subtests, test_file_name, test_file_path, IMAGE_NAME, step_progress="not started")
    event = s3sqs_event_maker(BUCKET_TEST, s3_key, QUEUE_TEST, receipt_handle)

    # execute lambda in local docker container
    with subtests.test(msg="execute docker lambda locally"):
        # Send a POST request to the Lambda function
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})

        # print docker logs
        print_container_logs(IMAGE_NAME)
        
        # check response successful, and tables / files look as they should given success
        check_success(subtests, response, file_id, s3_key_save)

    ### upload second time - rejection due to prior completion ###
    # execute lambda in local docker container
    with subtests.test(msg="execute docker lambda locally"):
        # Send a POST request to the Lambda function
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})

        # print docker logs
        print_container_logs(IMAGE_NAME)
        
        # Check the response
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["statusCode"] == 400
        body = json.loads(response_json["body"])
        message = body["message"]
        assert "file with file_id already exist" in message

    ### clean up files and tables ###
    clean_up(subtests, s3_key, s3_key_save, file_id)


def test_file_preprocess_in_progress(container_controller, subtests):
    # setup step
    file_id, request_id, s3_key, s3_key_save, receipt_handle = step_setup(subtests, test_file_name, test_file_path, IMAGE_NAME, step_progress="in progress")
    event = s3sqs_event_maker(BUCKET_TEST, s3_key, QUEUE_TEST, receipt_handle)

    # replace status "complete" with "in progress"
    read_response = read(FILE_LEDGER_TEMP, "file_id", file_id)
    read_status = read_response[0].get("status", None)
    read_status["receiver_step_1"] = "in progress"
    update_document = {"status": read_status}
    update(FILE_LEDGER_TEMP, "file_id", file_id, update_document)

    # execute lambda in local docker container
    with subtests.test(msg="execute docker lambda locally"):
        # Send a POST request to the Lambda function
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})

        # print docker logs
        print_container_logs(IMAGE_NAME)
        
        # Check the response
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["statusCode"] == 400
        body = json.loads(response_json["body"])
        message = body["message"]
        assert "file with file_id already exist" in message

    ### clean up files and tables ###
    clean_up(subtests, s3_key, s3_key_save, file_id)
    
    
def test_failure_previous_fail(container_controller, subtests):
    ### setup step ###
    file_id, request_id, s3_key, s3_key_save, receipt_handle = step_setup(subtests, test_file_name, test_file_path, IMAGE_NAME, step_progress="fail")
    event = s3sqs_event_maker(BUCKET_TEST, s3_key, QUEUE_TEST, receipt_handle)

    # execute lambda locally
    with subtests.test(msg="execute handler"):
        # Send a POST request to the Lambda function
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})

        # print docker logs
        print_container_logs(IMAGE_NAME)
        
        # Check the response
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["statusCode"] == 400
        body = json.loads(response_json["body"])
        message = body["message"]
        assert "file with file_id failed recently" in message

    # check that row in history-ledger table does not exist
    with subtests.test(msg="check that row for file_id not in history ledger"):
        response = read(HISTORY_LEDGER_MAIN, "file_id", file_id)
        assert len(response) > 0

    ### clean up ###
    clean_up(subtests, s3_key, s3_key_save, file_id)
    
    
def test_failure_hash_mismash(container_controller, subtests):
    ### setup step ###
    file_id_mismatch = "this is not the same hash as above"
    file_id, request_id, s3_key, s3_key_save, receipt_handle = step_setup(subtests, test_file_name, test_file_path, IMAGE_NAME, step_progress="not started", file_id_override=file_id_mismatch)
    event = s3sqs_event_maker(BUCKET_TEST, s3_key, QUEUE_TEST, receipt_handle)

    # execute lambda locally
    with subtests.test(msg="execute handler"):
        # Send a POST request to the Lambda function
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})

        # print docker logs
        print_container_logs(IMAGE_NAME)
        
        # Check the response
        assert response.status_code == 200
        response_json = response.json()
        print(f"response_json --> {response_json}")
        assert response_json["statusCode"] == 400
        body = json.loads(response_json["body"])
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
