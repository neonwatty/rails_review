import os
import json
import uuid
from receivers import s3_client
from decorators.warmer import warmer
from decorators.message import sqs_receiver_wrapper
from receivers.receiver_preprocess.audio_extractor import extract_audio
from receivers.receiver_preprocess.audio_extractor import check_file_size
from receivers.utilities.create_io_dir import local_input_file_path, local_output_file_path
from tables.public.row_update import update
from tables.public.row_create import create
from tables.public.row_read import read
from utilities.tools.hash import hash_file


STAGE = os.environ.get("STAGE", "dev")
FILE_LEDGER_TEMP = os.environ["FILE_LEDGER_TEMP"]
HISTORY_LEDGER_MAIN = os.environ["HISTORY_LEDGER_MAIN"]
LAMBDA_FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "local-test")


@warmer
@sqs_receiver_wrapper
def handler(event, context):
    # generate history_id
    history_id = str(uuid.uuid4())
    
    # generate request_id backup
    request_id = str(uuid.uuid4())
        
    # unpack required objects from event
    s3_bucket = event["s3"]["bucket"]["name"]
    s3_key = event["s3"]["object"]["key"]

    # deconstruct s3_key into stage, user_id, file_id, and file_name
    s3_key_split = s3_key.split("/")
    stage = s3_key_split[0]
    user_id = s3_key_split[1]
    file_id = s3_key_split[2]
    file_name = s3_key_split[3]

    # try function
    try:            
        # adjust local file paths to this bespoke function
        local_input_path = local_input_file_path    # extension added by moviepy to read video
        local_output_path = local_output_file_path + ".mp3"  # extension required for saving audio output

        # download file to lambda
        s3_client.download_file(s3_bucket, s3_key, local_input_path)
        print(f"SUCCESS: File downloaded to {local_input_path}")

        # get file hash
        hash = hash_file(local_input_path)

        # check if hash (file_id) already exists in temp file ledger
        read_response = read(FILE_LEDGER_TEMP, "file_id", hash)
        
        # if file_id row currently not in temp file ledger return
        if len(read_response) == 0:
            # update history ledger with no file_ledger row attempt
            document = {
                "request_id": request_id,
                "file_id": file_id,
                "user_id": user_id,
                "status_code": 400,
                "lambda_function_name": LAMBDA_FUNCTION_NAME,
                "exception": f"failed due to no row in temp file ledger - file_id is {hash}",
            }
            create(HISTORY_LEDGER_MAIN, "history_id", history_id, document)

            # return report of failure to client
            return {"statusCode": 400, "body": json.dumps({"request_id": request_id, "message": f"FAILURE: failed due to no row in temp file ledger - file_id is {hash}"})}
        
        # check if file_id row already complete or failed - if so delete and return
        read_status = read_response[0].get("status", None)
        request_id = read_response[0].get("request_id", None)
        receiver_preprocess = read_status["receiver_preprocess"]
                
        # if receiver_process already complete, return
        if receiver_preprocess == "complete" or receiver_preprocess == "in progress":
            return {"statusCode": 400, "body": json.dumps({"request_id": request_id, "message": "FAILURE: file with file_id already exists"})}

        # if receiver_process failed, add entry to history table for scheduled deletion
        if receiver_preprocess == "fail":  # SHOULD WE FAIL OUT HERE OR RE-TRY?
            # update history ledger with duplicate file update attempt
            document = {
                "request_id": request_id,
                "file_id": file_id,
                "user_id": user_id,
                "status_code": 400,
                "lambda_function_name": LAMBDA_FUNCTION_NAME,
                "exception": f"failed due to duplicate file upload attempt - file_id is {hash}",
            }
            create(HISTORY_LEDGER_MAIN, "history_id", history_id, document)

            # return report of failure to client
            return {"statusCode": 400, "body": json.dumps({"request_id": request_id, "message": "FAILURE: file with file_id failed recently"})}
        print("SUCCESS: file hash passed inspection")
        
        # set receiver_preprocess to "in progress" TODO
        read_status["receiver_preprocess"] = "in progress"
        update_document = {"status": read_status}
        update(FILE_LEDGER_TEMP, "file_id", file_id, update_document)
        
        # extract audio
        extract_audio(local_input_path, local_output_path)
        print(f"SUCCESS: Audio extracted to {local_output_path}")
        
        
        # Get the S3 object file size in mb - optional: check that file_size_mb is not greater than threshold
        # file_size_mb = check_file_size(s3_bucket, s3_key)

        # save file back to s3
        s3_key_save = f"{STAGE}/{user_id}/{file_id}/receiver_preprocess.mp3"
        s3_client.upload_file(local_output_path, s3_bucket, s3_key_save)
        print("SUCCESS: Audio uploaded to s3")
        
        # read in current document for file_id from temp file ledger
        read_response = read(FILE_LEDGER_TEMP, "file_id", file_id)
        document = read_response[0]
        del document["file_id"]
 
        document["status"]["receiver_preprocess"] = "complete"
        document["file_metadata"]["s3_data"]["files"]["receiver_preprocess"] = s3_key_save
                
        update(FILE_LEDGER_TEMP, "file_id", file_id, document)

        # uplaod finished file back to s3
        return {"statusCode": 200, "body": json.dumps({"s3_key_save": s3_key_save, "user_id": user_id, "file_id": file_id, "request_id": request_id})}
    except Exception as e:
        # print failure message
        print(str(e))

        # report failure to history ledger
        document = {"request_id": request_id, "file_id": file_id, "user_id": user_id, "status_code": 500,  "lambda_function_name": LAMBDA_FUNCTION_NAME, "exception": str(e)}
        create(HISTORY_LEDGER_MAIN, "history_id", history_id, document)

        return {"statusCode": 500, "body": json.dumps({"request_id": request_id, "message": str(e)})}
