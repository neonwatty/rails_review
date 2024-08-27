import pytest
import os
import json
import time
import requests
import uuid
from utilities.tools.hash import hash_file
from entrypoints.utilities.file_type_validator import valid_file_types
from entrypoints.utilities.upload_file_name_validator import MAX_UPLOAD_FILE_NAME_LENGTH
from tests.utilities.execute_subprocess import execute_subprocess_command
from tables.secrets.row_read import read as read_secrets
from tables.gateway.row_read import read as read_gateway
from tables.public.row_read import read
from tables.public.row_destroy import destroy
from s3.object_exist import exist
from s3.object_delete import delete
from tests.utilities.docker_utilities import print_container_logs

# assign current directory
current_directory = os.getcwd()
home_dir = os.path.expanduser("~")

# define docker variables
DOCKER_PORT = 9000
LAMBDA_ENDPOINT = f"http://localhost:{DOCKER_PORT}/2015-03-31/functions/function/invocations"

# Define your test parameters
STAGE = os.environ.get("STAGE", "dev")
BUCKET_TEST = os.environ["BUCKET_TEST"]
IMAGE_NAME = "entrypoint_input"
LAMBDA_FUNCTION_NAME = f"entrypoints-{STAGE}-{IMAGE_NAME}"
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
def docker_controller():
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
    time.sleep(5)

    yield

    # stop and remove container
    command = ["docker", "stop", IMAGE_NAME]
    stdout = execute_subprocess_command(command)

    command = ["docker", "rm", IMAGE_NAME]
    stdout = execute_subprocess_command(command)


def test_success(docker_controller, subtests, shared_state):
    # check that user's api key maps to a present api id
    with subtests.test("check that user has valid api key, maps to current api id"):
        # grab api_id associated with user
        api_id = read_secrets(USER_ID)["Item"]["api_id"]

        # check that api_id exists in gateway table
        response = read_gateway(api_id)
        response_keys = list(response.keys())
        assert "Item" in response_keys

    # execute lambda in local docker container
    with subtests.test(msg="execute entrypoint via docker lambda locally - with success"):
        # construct payload / event
        request_id = str(uuid.uuid4())
        payload = {"action": "upload_test", "fileData": test_file, "fileType": valid_file_types[0], "fileHash": test_file_hash}
        event = {}
        event["user_id"] = USER_ID
        event["request_id"] = request_id
        event["body"] = json.dumps(payload)
        event["headers"] = {}
        event["headers"]["appApiKey"] = read_secrets(USER_ID)["Item"]["api_key"]

        # Send a POST request to the Lambda function to execute entrypoint
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})

        # print docker logs
        print_container_logs(IMAGE_NAME)

        # Check for successful response
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["statusCode"] == 200

        # grab response body
        body = json.loads(response_json["body"])

        # assert presigned_data in body and store in shared_state
        assert "presigned_data" in list(body.keys())
        presigned_data = body["presigned_data"]
        shared_state["presigned_data"] = presigned_data

        # store file_id in shared_state
        file_id = body["file_id"]
        shared_state["file_id"] = file_id

    ### fail out if same hash is sent a second time ###
    with subtests.test(msg="execute entrypoint with docker locally - with failure - attempt to upload the same file id again"):
        # Send a POST request to the Lambda function
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})

        # print docker logs
        print_container_logs(IMAGE_NAME)
        
        # Check for failed response
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["statusCode"] == 500

        # unpack body - assert that "already exists" present in return message
        body = json.loads(response_json["body"])
        message = body["message"]
        assert "already exists" in message

    # check that row in history-ledger table now exists (associated with process file_id)
    with subtests.test(msg="check that row in history table for file_id now exists"):
        response = read(HISTORY_LEDGER_MAIN, "file_id", shared_state["file_id"])
        assert len(response) > 0, f"FAILURE: cannot find row in temp file-ledger table with file_id {file_id}"

    # delete row from file-ledger table associated with file_id
    with subtests.test(msg="delete row in history table for file_id"):
        response = destroy(HISTORY_LEDGER_MAIN, "file_id", shared_state["file_id"])
        assert response is True, f"FAILURE: failed to delete row in file-ledger table with file_id {file_id}"

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
def test_payload_failures(docker_controller, payload):
    # construct payload / event
    request_id = str(uuid.uuid4())
    event = {}
    event["user_id"] = USER_ID
    event["request_id"] = request_id
    event["body"] = json.dumps(payload)
    event["authorizationToken"] = read_secrets(USER_ID)["Item"]["api_key"]

    # Send a POST request to the Lambda function to execute entrypoint
    response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})

    # print docker logs
    print_container_logs(IMAGE_NAME)
        
    # Check for successful response
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["statusCode"] == 500


# test for failure based on duplicate file_id being uploaded
# TODO: adjust to allow for main ledger return of already processed data
def test_failure_duplicate_file_ids(docker_controller, subtests, shared_state):
    # execute entrypoint - 2x the same file_id
    with subtests.test(msg="execute entrypoint input check"):
        # grab api_key associated with user
        request_id = str(uuid.uuid4())

        # construct payload
        payload = {"action": "upload_test", "fileData": "test.mp4", "fileType": valid_file_types[0], "fileHash": test_file_hash}

        # upload file first time
        event = {}
        event["user_id"] = USER_ID
        event["request_id"] = request_id
        event["body"] = json.dumps(payload)
        event["headers"] = {}
        event["headers"]["appApiKey"] = read_secrets(USER_ID)["Item"]["api_key"]

        # Send a POST request to the Lambda function to execute entrypoint
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})

        # print docker logs
        print_container_logs(IMAGE_NAME)
        
        # Check for successful response
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["statusCode"] == 200
        body = json.loads(response_json["body"])
        file_id = body["file_id"]
        shared_state["file_id"] = file_id

        # upload second time
        response = requests.post(LAMBDA_ENDPOINT, data=json.dumps(event), headers={"Content-Type": "application/json"})
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["statusCode"] == 500
        body = json.loads(response_json["body"])
        message = body["message"]
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
        assert len(response) > 0, f"FAILURE: cannot find row in temp file-ledger table with file_id {file_id}"

    # delete row from file-ledger table associated with file_id
    with subtests.test(msg="delete row in history table for file_id"):
        response = destroy(HISTORY_LEDGER_MAIN, "file_id", shared_state["file_id"])
        assert response is True, f"FAILURE: failed to delete row in file-ledger table with file_id {file_id}"

    # check that file_id not listed in history ledger
    with subtests.test(msg="check that row for file_id not in history ledger"):
        response = read(HISTORY_LEDGER_MAIN, "file_id", shared_state["file_id"])
        assert len(response) == 0
