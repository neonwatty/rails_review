import pytest
import os
import requests
import uuid
import boto3
import time
from utilities.tools.hash import hash_file
from entrypoints.utilities.file_type_validator import valid_file_types
from tables.secrets.row_read import read as read_secrets
from tables.public.row_read import read
from tables.public.row_destroy import destroy
from s3.subdir_delete import list_subdir, delete_subdir
from tests.utilities.execute_subprocess import execute_subprocess_command
from tests.utilities.receiver_utilities import clean_up


# endpoint definition
GATEWAY_ENDPOINT = os.getenv("GATEWAY_ENDPOINT")
LAMBDA_ENDPOINT = f"{GATEWAY_ENDPOINT}/entrypoint_input"

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
STAGE = os.environ.get("STAGE", "development")
BUCKET_TEST = os.environ["BUCKET_TEST"]
BUCKET_TRIGGER = os.environ["BUCKET_TRIGGER"]
BUCKET_MAIN = os.environ["BUCKET_MAIN"]
IMAGE_NAME = "entrypoint_input"
LAMBDA_FUNCTION_NAME = f"entrypoints-{STAGE}-{IMAGE_NAME}"
SERVERLESS_NAME = "serverless_entrypoints.yml"
QUEUE_TEST = f"{os.environ["APP_NAME"]}-test"
USER_ID = os.getenv("USER_ID_TEST_1")
FILE_LEDGER_TEMP = os.environ["FILE_LEDGER_TEMP"]
FILE_LEDGER_MAIN = os.environ["FILE_LEDGER_MAIN"]
HISTORY_LEDGER_MAIN = os.environ["HISTORY_LEDGER_MAIN"]

# images to build and deploy
images = ["entrypoint_input", "receiver_preprocess", "receiver_step_1", "receiver_end"]

# serverless yamls to (re)-deploy
yamls = ["serverless_entrypoints.yml", "serverless_receivers.yml"]

# test file data
test_file_name = "entrypoint_input.mp4"
test_file_path = "tests/test_files/test_file.mp4"
test_file_hash = hash_file(test_file_path)


@pytest.fixture
def shared_state():
    # Initialize shared state
    state = {"file_id": None, "presigned_data": None, "s3_data": None}
    yield state


@pytest.fixture(scope="module")
def build_deploy():
    # build and deploy images
    for image in images:
        command = ["bash", "build_image.sh", STAGE, image]
        stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")
    
        command = ["bash", "deploy_image.sh", STAGE, image]
        stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")
        
    time.sleep(5)
    
    # deploy yamls
    for yam in yamls:
        command = ["bash", "adjust_functions.sh", "deploy", STAGE, yam]
        stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas")


def test_success(build_deploy, subtests, shared_state):
    # execute lambda in local docker container
    with subtests.test(msg="execute entrypoint via cloud lambda - with success"):
        # grab api_key associated with user
        API_KEY = read_secrets(USER_ID)["Item"]["api_key"]

        # construct payload / event
        request_id = str(uuid.uuid4())

        # construct payload and headers
        payload = {
            "action": "upload",
            "fileData": test_file_name,
            "fileType": valid_file_types[0],
            "fileHash": test_file_hash,
            "request_id": request_id,
        }
        headers = {"Content-Type": "text/plain", "appApiKey": API_KEY}

        # Send a POST request to the Lambda function to execute entrypoint
        response = requests.post(LAMBDA_ENDPOINT, headers=headers, json=payload, timeout=60)

        # Check for successful response
        assert response.status_code == 200
        response_json = response.json()
        assert "presigned_data" in list(response_json.keys())
        presigned_data = response_json["presigned_data"]
        shared_state["presigned_data"] = presigned_data

        # store file_id in shared_state
        file_id = response_json["file_id"]
        shared_state["file_id"] = file_id
        
    # upload file to presigned_data location returned by entrypoint
    with subtests.test(msg="upload test file using presigned data"):
        # unpack presigned data
        url = shared_state["presigned_data"]["url"]
        fields = shared_state["presigned_data"]["fields"]

        # post file to s3 location provided by presigned data
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path, f)}
            upload_response = requests.post(url, data=fields, files=files, timeout=30)
            assert upload_response.status_code == 204

    # sleep for 30 secs to allow for pipeline processing
    time.sleep(30)

    # check in on main file ledger to see if data has been copied there yet
    with subtests.test(msg="check that receiver_end complete"):
        # Duration and interval
        total_duration = 60  # Total duration to check the condition (in seconds)
        check_interval = 5   # Interval between checks (in seconds)
        complete_check = 1

        # Check that row in file-ledger table now exists (associated with process file_id)
        start_time = time.time()
        while time.time() - start_time < total_duration:
            with subtests.test(msg="check that row in table for file_id now exists"):
                main_response = read(FILE_LEDGER_MAIN, "file_id", file_id)
                if len(main_response) > 0:
                    # assert that temp file ledger is clear of file_id row
                    temp_response = read(FILE_LEDGER_TEMP, "file_id", file_id)
                    assert len(temp_response) == 0
                    
                    # look for all steps in status
                    status = main_response[0]["status"]
                    status_keys = list(status.keys())
                    assert "entrypoint_input" in status_keys
                    assert "receiver_preprocess" in status_keys
                    assert "receiver_step_1" in status_keys
                    assert "receiver_end" in status_keys
                    
                    # look for completion of final step
                    receiver_preprocess = status["receiver_end"]
                    if receiver_preprocess == "complete":
                        complete_check = 0
                        break
            # Wait before the next check
            time.sleep(check_interval)
        if complete_check == 1:
            # If the loop completes without breaking, the condition was not met
            assert False, "Condition not met within the allowed time frame"
        
    # clean up objects
    with subtests.test(msg="remove objects from main bucket"):
        # get bucket and subdir name to delete files
        response = read(FILE_LEDGER_MAIN, "file_id", file_id)
        delete_bucket = response[0]["file_metadata"]["s3_data"]["bucket_name"]
        subdir = response[0]["file_metadata"]["s3_data"]["subdir"]
        
        # check that delete subdir is not empty
        list_response = list_subdir(delete_bucket, subdir)
        assert len(list_response) > 0

        # delete subdir of files
        delete_response = delete_subdir(delete_bucket, subdir)
        assert delete_response is None
        
        # double check delete subdir is empty
        list_response = list_subdir(delete_bucket, subdir)
        assert len(list_response) == 0
        
    # clean up main file ledger
    with subtests.test(msg="delete row of file_id from main file ledger"):
        destroy_response = destroy(FILE_LEDGER_MAIN, "file_id", file_id)
        assert destroy_response is True