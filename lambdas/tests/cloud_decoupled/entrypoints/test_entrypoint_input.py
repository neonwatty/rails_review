import pytest
import os
import requests
import uuid
import boto3
from utilities.tools.hash import hash_file
from entrypoints.utilities.file_type_validator import valid_file_types
from entrypoints.utilities.upload_file_name_validator import MAX_UPLOAD_FILE_NAME_LENGTH
from tables.secrets.row_read import read as read_secrets
from tables.public.row_read import read
from tables.public.row_destroy import destroy
from s3.object_exist import exist
from s3.object_delete import delete
from tests.utilities.execute_subprocess import execute_subprocess_command

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
STAGE = os.environ.get("STAGE", "dev")
BUCKET_TEST = os.environ["BUCKET_TEST"]
IMAGE_NAME = "entrypoint_input"
LAMBDA_FUNCTION_NAME = f"entrypoints-{STAGE}-{IMAGE_NAME}"
SERVERLESS_NAME = "serverless_entrypoints.yml"
QUEUE_TEST = os.environ["QUEUE_TEST"]
USER_ID = os.getenv("USER_ID_TEST_1")
FILE_LEDGER_TEMP = os.environ["FILE_LEDGER_TEMP"]
HISTORY_LEDGER_MAIN = os.environ["HISTORY_LEDGER_MAIN"]

# test file data
test_file = "blank.mp4"
test_file_path = "tests/test_files/blank.mp4"
test_file_hash = hash_file(test_file_path)


@pytest.fixture
def shared_state():
    # Initialize shared state
    state = {"file_id": None, "presigned_data": None, "s3_data": None}
    yield state


@pytest.fixture(scope="module")
def build_deploy():
    # build image
    command = ["bash", "build_image.sh", STAGE, IMAGE_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")

    # deploy image
    command = ["bash", "deploy_image.sh", STAGE, IMAGE_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")

    # deploy lambdas
    command = ["bash", "adjust_functions.sh", "deploy", STAGE, SERVERLESS_NAME]
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
            "action": "upload_test",
            "fileData": test_file,
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

    # check that row in history-ledger table now exists (associated with process file_id)
    with subtests.test(msg="check that row in history table for file_id now exists"):
        response = read(HISTORY_LEDGER_MAIN, "file_id", shared_state["file_id"])
        assert len(response) == 0, f"FAILURE: cannot find row in temp file-ledger table with file_id {file_id}"

    # check that row in file-ledger table now exists (associated with process file_id)
    with subtests.test(msg="check that row in temp table for file_id now exists"):
        # read file ledger row
        response = read(FILE_LEDGER_TEMP, "file_id", shared_state["file_id"])

        # check for newly created row
        assert len(response) > 0, f"FAILURE: cannot find row in temp file-ledger table with file_id {shared_state["file_id"]}"

        # unpack
        file_metadata = response[0]["file_metadata"]
        file_metadata_keys = list(file_metadata.keys())
        status = response[0]["status"]

        # ensure row contains s3 file location, store in shared state
        assert "s3_data" in file_metadata_keys
        s3_data = file_metadata["s3_data"]
        shared_state["s3_data"] = s3_data

        # ensure action is correct
        assert file_metadata["action"] == "upload_test"

        # assert values exist in status
        assert status["entrypoint_input"] == "complete"

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

    # check that file exists on s3
    with subtests.test("check that test file exists in s3"):
        response = exist(shared_state["s3_data"]["bucket_name"], shared_state["s3_data"]["files"]["entrypoint_input"])
        assert response is True

    # delete test file
    with subtests.test(msg="delete test file"):
        response = delete(shared_state["s3_data"]["bucket_name"], shared_state["s3_data"]["files"]["entrypoint_input"])
        assert response is True
        response = exist(shared_state["s3_data"]["bucket_name"], shared_state["s3_data"]["files"]["entrypoint_input"])
        assert response is False

    # delete row from file-ledger table associated with file_id
    with subtests.test(msg="delete row in table for file_id"):
        response = destroy(FILE_LEDGER_TEMP, "file_id", shared_state["file_id"])
        assert response is True

    # check that row in file-ledger table does not exists (associated with process file_id)
    with subtests.test(msg="check that row in temp table for file_id now exists"):
        # read file ledger row
        response = read(FILE_LEDGER_TEMP, "file_id", shared_state["file_id"])
        assert len(response) == 0


payload_failures = [
    {"action": "invalid_action", "fileData": "test.mp4", "fileType": valid_file_types[0], "fileHash": hash_file("tests/test_files/blank.mp4")},
    {
        "action": "upload_test",
        "fileData": "s" * (MAX_UPLOAD_FILE_NAME_LENGTH + 1),
        "fileType": valid_file_types[0],
        "fileHash": hash_file("tests/test_files/blank.mp4"),
    },
    {"action": "upload_test", "fileData": "test.mp4", "fileType": valid_file_types[0], "fileHash": "not_a_hash"},
]


# test various input event failures - bypassing auth, direct test on main
@pytest.mark.parametrize("payload", payload_failures)
def test_payload_failures(build_deploy, payload):
    # grab api_key associated with user
    API_KEY = read_secrets(USER_ID)["Item"]["api_key"]

    # construct payload / event
    request_id = str(uuid.uuid4())

    # construct payload and headers
    payload["request_id"] = request_id
    headers = {"Content-Type": "text/plain", "appApiKey": API_KEY}

    # Send a POST request to the Lambda function to execute entrypoint
    response = requests.post(LAMBDA_ENDPOINT, headers=headers, json=payload, timeout=60)

    # Check for successful response
    assert response.status_code == 500


# test for failure based on duplicate file_id being uploaded
# TODO: adjust to allow for main ledger return of already processed data
def test_failure_duplicate_file_ids(build_deploy, subtests, shared_state):
    with subtests.test(msg="execute entrypoint via cloud lambda - with success"):
        # grab api_key associated with user
        API_KEY = read_secrets(USER_ID)["Item"]["api_key"]

        # construct payload / event
        request_id = str(uuid.uuid4())

        # construct payload and headers
        payload = {
            "action": "upload_test",
            "fileData": test_file,
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

    ### fail out if same hash is sent a second time ###
    with subtests.test(msg="execute entrypoint with cloud lambda - with failure - attempt to upload the same file id again"):
        # Send a POST request to the Lambda function
        response = requests.post(LAMBDA_ENDPOINT, headers=headers, json=payload, timeout=60)

        # Check for failed response
        assert response.status_code == 500
        response_json = response.json()
        message = response_json["message"]
        assert "already exists" in message

    # check that row in file-ledger table now exists (associated with process file_id)
    with subtests.test(msg="check that row in temp table for file_id now exists"):
        response = read(FILE_LEDGER_TEMP, "file_id", shared_state["file_id"])
        assert len(response) > 0, f"FAILURE: cannot find row in temp file-ledger table with file_id {file_id}"

    # delete row from file-ledger table associated with file_id
    with subtests.test(msg="delete row in table for file_id"):
        response = destroy(FILE_LEDGER_TEMP, "file_id", shared_state["file_id"])
        assert response is True, f"FAILURE: failed to delete row in file-ledger table with file_id {file_id}"

    # check that row in history-ledger table now exists (associated with process file_id)
    with subtests.test(msg="check that row in history table for file_id now exists"):
        response = read(HISTORY_LEDGER_MAIN, "file_id", shared_state["file_id"])
        assert len(response) > 0, f"FAILURE: cannot find row in temp history-ledger table with file_id {file_id}"

    # delete row from file-ledger table associated with file_id
    with subtests.test(msg="delete row in history table for file_id"):
        response = destroy(HISTORY_LEDGER_MAIN, "file_id", shared_state["file_id"])
        assert response is True, f"FAILURE: failed to delete row in file-ledger table with file_id {file_id}"

    # check that file_id not listed in history ledger
    with subtests.test(msg="check that row for file_id not in history ledger"):
        response = read(HISTORY_LEDGER_MAIN, "file_id", shared_state["file_id"])
        assert len(response) == 0
