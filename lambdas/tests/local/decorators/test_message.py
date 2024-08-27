import json
import pytest
from unittest.mock import patch
from decorators.message import sqs_receiver_wrapper
from tests.utilities.receiver_utilities import s3sqs_event_maker



# Mocked SQS message_delete function
@patch("decorators.message.message_delete")
def test_sqs_message_handler_success(mock_message_delete):
    # Mocking the message_delete to return True
    mock_message_delete.return_value = True

    # Sample event and context
    bucket_name = "test_bucket"
    s3_key = "test_file"
    queue_name = "test_queue"
    receipt_handle = "12345"
    event = s3sqs_event_maker(bucket_name, s3_key, queue_name, receipt_handle)  
    context = {}

    @sqs_receiver_wrapper
    def mock_process_message(message, receipt_handle):
        # Simulate successful message processing
        return {"statusCode": 200}

    # Act
    result = mock_process_message(event, context)

    # Assert
    assert result["statusCode"] == 200

    mock_message_delete.assert_called_once_with(queue_name, receipt_handle)


@patch("decorators.message.message_delete")
def test_sqs_message_handler_failure_processing(mock_message_delete):
    # Mocking the message_delete to return True
    mock_message_delete.return_value = True

    # Sample event and context
    bucket_name = "test_bucket"
    s3_key = "test_file"
    queue_name = "test_queue"
    receipt_handle = "12345"
    event = s3sqs_event_maker(bucket_name, s3_key, queue_name, receipt_handle)  
    context = {}

    @sqs_receiver_wrapper
    def mock_process_message(message, receipt_handle):
        # Simulate failed message processing
        a = 2
        a += "b"

    # Act
    result = mock_process_message(event, context)

    # Assert
    assert result["statusCode"] > 200

    mock_message_delete.assert_not_called()


@patch("decorators.message.message_delete")
def test_sqs_message_handler_failure_deletion(mock_message_delete):
    # Mocking the message_delete to return False
    mock_message_delete.return_value = False
    
    # Sample event and context
    bucket_name = "test_bucket"
    s3_key = "test_file"
    queue_name = "test_queue"
    receipt_handle = "12345"
    event = s3sqs_event_maker(bucket_name, s3_key, queue_name, receipt_handle)  
    context = {}

    @sqs_receiver_wrapper
    def mock_process_message(message, receipt_handle):
        # Simulate successful message processing
        return {"statusCode": 200}

    # Act
    result = mock_process_message(event, context)

    # Assert
    assert result == {"statusCode": 400, "body": json.dumps("BAD REQUEST: Error processing SQS message")}
    mock_message_delete.assert_called_once_with(queue_name, receipt_handle)


@patch("decorators.message.message_delete")
def test_sqs_message_handler_exception_handling(mock_message_delete):
    # Mocking the message_delete to raise an exception
    mock_message_delete.side_effect = Exception("Deletion failed")

    # Sample event and context
    bucket_name = "test_bucket"
    s3_key = "test_file"
    queue_name = "test_queue"
    receipt_handle = "12345"
    event = s3sqs_event_maker(bucket_name, s3_key, queue_name, receipt_handle)  
    context = {}

    @sqs_receiver_wrapper
    def mock_process_message(message, receipt_handle):
        # Simulate successful message processing
        return {"statusCode": 200}

    # Act
    result = mock_process_message(event, context)

    # Act
    assert result == {"statusCode": 500, "body": json.dumps("BAD REQUEST: Error processing SQS message: Deletion failed")}

    # Assert
    mock_message_delete.assert_called_once_with(queue_name, receipt_handle)
