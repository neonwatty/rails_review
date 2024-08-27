import os
import json
import uuid
from unittest.mock import patch
from decorators.auth import auth_confirm
from tables.secrets.row_read import read

# import test user_id
USER_ID = os.getenv("USER_ID_TEST_1")


@patch("decorators.auth.read_api_key", return_value={"user_id": "user123"})
def test_successful_mock_api_key(mock_read):
    @auth_confirm
    def sample_function(event, context):
        return {"statusCode": 200, "body": json.dumps({"message": "Success", "user_id": event["user_id"]})}

    event = {"headers": {"appApiKey": "api123"}, "body": "some body content"}
    context = {}

    # Act
    response = sample_function(event, context)

    # Assert
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "Success"
    assert "user_id" in event
    assert "request_id" in event


def test_missing_headers():
    @auth_confirm
    def sample_function(event, context):
        return {"statusCode": 200, "body": json.dumps({"message": "Success"})}

    event = {"body": "some body content"}
    context = {}

    response = sample_function(event, context)
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body["message"][1:-1] == "FAILURE: 'headers' not found in event"


def test_missing_appApiKey():
    @auth_confirm
    def sample_function(event, context):
        return {"statusCode": 200, "body": json.dumps({"message": "Success"})}

    event = {"headers": {}, "body": "some body content"}
    context = {}

    response = sample_function(event, context)
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body["message"][1:-1] == "FAILURE: 'appApiKey' not found in headers"
    assert "request_id" in body


@patch("decorators.auth.read_api_key", return_value={})
def test_user_id_not_found(mock_read):
    @auth_confirm
    def sample_function(event, context):
        return {"statusCode": 200, "body": json.dumps({"message": "Success"})}

    event = {"headers": {"appApiKey": '"api123"'}, "body": "some body content"}
    context = {}

    # Act
    response = sample_function(event, context)

    # Assert
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body["message"] == "FAILURE: 'user_id' is None"
    assert "request_id" in body  # Check if request_id is in the response


@patch("decorators.auth.read_api_key", return_value={"user_id": "user123"})
def test_exception_handling(mock_read):
    @auth_confirm
    def sample_function(event, context):
        raise ValueError("Test exception")

    event = {"headers": {"appApiKey": "api123"}, "body": "some body content"}
    context = {}

    response = sample_function(event, context)
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body["message"].startswith("Test exception")


def test_complete_auth():
    # grab api_key associated with user
    API_KEY = read(USER_ID)["Item"]["api_key"]

    # create request_id
    request_id = str(uuid.uuid4())

    # create function decorated with auth
    @auth_confirm
    def sample_function(event, context):
        return {"statusCode": 200, "body": {"message": "Success", "user_id": USER_ID, "request_id": request_id}}

    event = {"headers": {"appApiKey": API_KEY}, "body": "some body content"}
    context = {}

    # Act
    response = sample_function(event, context)

    # Assert
    assert response["statusCode"] == 200
    body = response["body"]
    assert body["message"] == "Success"
    assert "user_id" in event
    assert "request_id" in event
