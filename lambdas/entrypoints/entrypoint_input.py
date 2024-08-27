import json
import os
import uuid
from decorators.warmer import warmer
from decorators.auth import auth_confirm
from entrypoints.utilities.payload_validator import validator as payload_validator
from tables.public.row_create import create
from tables.public.row_read import read
from s3.object_add import add


STAGE = os.environ.get("STAGE", "dev")
FILE_LEDGER_TEMP = os.environ["FILE_LEDGER_TEMP"]
FILE_LEDGER_MAIN = os.environ["FILE_LEDGER_MAIN"]
QUEUE_TEST = os.environ["QUEUE_TEST"]
BUCKET_TEST = os.environ["BUCKET_TEST"]
BUCKET_TRIGGER = os.environ["BUCKET_TRIGGER"]
HISTORY_LEDGER_MAIN = os.environ["HISTORY_LEDGER_MAIN"]
LAMBDA_FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "local-test")


def main(event, context):
    # upnpack required args from event
    user_id = event["user_id"]
    request_id = event["request_id"]
    payload = json.loads(event["body"])
    action = payload["action"]
    file_data = payload["fileData"]
    file_type = payload["fileType"]
    file_id = payload["fileHash"]

    # create request_id
    request_id = str(uuid.uuid4())

    # create history_id in case of failure
    history_id = str(uuid.uuid4())

    # try functions
    try:
        # validate payload args
        payload_check, payload_message = payload_validator(action, file_data, file_type, file_id)
        if payload_check is False:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"request_id": request_id, "message": payload_message, "user_id": user_id}),
            }

        # check if file_hash already exists in ledger
        rows = read(FILE_LEDGER_TEMP, "file_id", file_id)
        if len(rows) > 0:
            # NOTE: this should not returned processed data as it indicates the same file is still processing
            raise ValueError(f"FAILURE: file with file_id already exists {file_id}")
        rows = read(FILE_LEDGER_MAIN, "file_id", file_id)
        if len(rows) > 0:
            # TODO: instead of throwing error this can return already processed output
            raise ValueError(f"FAILURE: file with file_id already exists {file_id}")

        # bucket name switch
        bucket_name = BUCKET_TEST
        if action == "upload":
            bucket_name = BUCKET_TRIGGER
        
        # collect presigned url
        filename = "entrypoint_input.mp4"
        presigned_post_url_results = add(user_id, file_id, filename, bucket_name, stage=STAGE)
        subdir = f"{STAGE}/{user_id}/{file_id}"
        key = f"{STAGE}/{user_id}/{file_id}/{filename}"

        # unapck presigned
        url = presigned_post_url_results["url"]
        fields = presigned_post_url_results["fields"]

        # package upload_data
        presigned_data = {"url": url, "fields": fields}
        s3_data = {"bucket_name": bucket_name, "subdir": subdir, "files": {"entrypoint_input": key}}

        # update temp ledger
        document = {
            "user_id": user_id,
            "request_id": request_id,
            "status": {"entrypoint_input": "complete", "receiver_preprocess": "not started", "receiver_step_1": "not started", "receiver_end": "not started"},
            "file_metadata": {"action": action, "presigned_data": presigned_data, "s3_data": s3_data},
        }

        # create row in temp file ledger
        create(FILE_LEDGER_TEMP, "file_id", file_id, document)

        print("SUCCESS: entrypoint_input ran successfully")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"file_id": file_id, "request_id": request_id, "presigned_data": presigned_data, "message": "SUCCESS: request succeeded"}
            ),
        }
    except Exception as e:
        # create failure messgage
        print(str(e))

        # send failure message to history ledger
        document = {"request_id": request_id, "file_id": file_id, "user_id": user_id, "status_code": 500, "lambda_function_name": LAMBDA_FUNCTION_NAME, "exception": str(e)}
        create(HISTORY_LEDGER_MAIN, "history_id", history_id, document)

        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"request_id": request_id, "queue_id": None, "message": str(e)}),
        }


@warmer
@auth_confirm
def handler(event, context):
    result = main(event, context)
    return result
