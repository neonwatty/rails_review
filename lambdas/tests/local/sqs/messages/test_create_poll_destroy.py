# from sqs.messages.message_create import message_create
# from sqs.messages.message_delete import message_delete
# from sqs.messages.message_poll import message_poll
# import os
# import time
# import pytest
# from dotenv import load_dotenv

# load_dotenv("./.env")

# QUEUE_TEST = f"{os.environ["APP_NAME"]}-test"
# QUEUE_RECEIVER_PREPROCESS = os.environ["QUEUE_RECEIVER_PREPROCESS"]
# QUEUE_RECEIVER_STEP_1 = os.environ["QUEUE_RECEIVER_STEP_1"]
# QUEUE_RECEIVER_END = os.environ["QUEUE_RECEIVER_END"]

# queue_names = [QUEUE_TEST, QUEUE_RECEIVER_PREPROCESS, QUEUE_RECEIVER_STEP_1, QUEUE_RECEIVER_END]

# test_payload = {"test_input": "this is a test"}


# @pytest.mark.parametrize("queue_name", queue_names)
# def test_message(queue_name, subtests):
#     message_id = None
#     receipt_handle = None

#     with subtests.test(msg="create"):
#         response = message_create(queue_name, test_payload)
#         assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
#         message_id = response["MessageId"]

#     with subtests.test(msg="poll"):
#         receipt_handle = message_poll(queue_name, message_id)
#         assert receipt_handle is not None

#     with subtests.test(msg="delete"):
#         receipt_handle = message_delete(queue_name, receipt_handle)
