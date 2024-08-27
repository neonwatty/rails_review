import os
import json
import uuid
from decorators.warmer import warmer
from decorators.message import sqs_receiver_wrapper
from receivers.utilities.create_io_dir import local_input_path
from tables.public.row_update import update
from tables.public.row_create import create
from tables.public.row_destroy import destroy
from tables.public.row_read import read
from s3.client_utilities import list_subdir, upload, download, delete


STAGE = os.environ.get("STAGE", "dev")
FILE_LEDGER_TEMP = os.environ["FILE_LEDGER_TEMP"]
FILE_LEDGER_MAIN = os.environ["FILE_LEDGER_MAIN"]
BUCKET_MAIN = os.environ["BUCKET_MAIN"]
BUCKET_TEST = os.environ["BUCKET_TEST"]
BUCKET_TRIGGER = os.environ["BUCKET_TRIGGER"]
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
        # check if (file_id) already exists in temp file ledger
        read_response = read(FILE_LEDGER_TEMP, "file_id", file_id)

        # if file_id row currently not in temp file ledger return
        if len(read_response) == 0:
            # update history ledger with no file_ledger row attempt
            document = {
                "request_id": request_id,
                "file_id": file_id,
                "user_id": user_id,
                "status_code": 400,
                "lambda_function_name": LAMBDA_FUNCTION_NAME,
                "exception": f"failed due to no row in temp file ledger - file_id is {file_id}",
            }
            create(HISTORY_LEDGER_MAIN, "history_id", history_id, document)

            # return report of failure to client
            return {"statusCode": 400, "body": json.dumps({"request_id": request_id, "message": f"FAILURE: failed due to no row in temp file ledger - file_id is {file_id}"})}

        # check if file_id row already complete or failed - if so delete and return
        read_status = read_response[0].get("status", None)
        request_id = read_response[0].get("request_id", None)
        file_metadata = read_response[0].get("file_metadata", None)
        action = file_metadata["action"]
        receiver_prev_progress = read_status["receiver_end"]
                
        # if receiver_process already complete, return
        if receiver_prev_progress == "complete" or receiver_prev_progress == "in progress":
            return {"statusCode": 400, "body": json.dumps({"request_id": request_id, "message": "FAILURE: file with file_id already exists"})}

        # if receiver_process failed, add entry to history table for scheduled deletion
        if receiver_prev_progress == "fail":  # SHOULD WE FAIL OUT HERE OR RE-TRY?
            # update history ledger with duplicate file update attempt
            document = {
                "request_id": request_id,
                "file_id": file_id,
                "user_id": user_id,
                "status_code": 400,
                "lambda_function_name": LAMBDA_FUNCTION_NAME,
                "exception": f"failed due to duplicate file upload attempt - file_id is {file_id}",
            }
            create(HISTORY_LEDGER_MAIN, "history_id", history_id, document)

            # return report of failure to client
            return {"statusCode": 400, "body": json.dumps({"request_id": request_id, "message": "FAILURE: file with file_id failed recently"})}
        print("SUCCESS: file_id passed inspection")
        
        # set receiver_preprocess to "in progress"
        read_status["receiver_end"] = "in progress"
        update_document = {"status": read_status}
        update(FILE_LEDGER_TEMP, "file_id", file_id, update_document)
        
        # set final bucket detination based on action
        final_s3_bucket_destination = BUCKET_MAIN
        final_file_ledger_destination = FILE_LEDGER_MAIN
        if "test" in action:
            final_s3_bucket_destination = BUCKET_TEST
            final_file_ledger_destination = FILE_LEDGER_TEMP
        
        ### transfer files from temp bucket to main ###
        # list out all contents of s3 subdirectory
        s3_subdir = f"{stage}/{user_id}/{file_id}"
        s3_subdir_files = list_subdir(s3_bucket, s3_subdir)
        
        # loop over all files and transfer to final destination bucket
        # update document for file ledger
        for s3_file_record in s3_subdir_files:
            # create file name for local version
            s3_file_record_name = s3_file_record["Key"]
            local_s3_file_name = s3_file_record_name.split('/')[-1]
            local_file_path = local_input_path + "/" + local_s3_file_name
            
            # download to this machine
            download_val = download(s3_bucket, s3_file_record_name, local_file_path)
            if download_val is False:
                raise ValueError(f"FAILURE: file was not downloaded correctly -> bucket: {s3_bucket}, file: {s3_file_record_name}")
            
            # push to new location
            upload_val = upload(final_s3_bucket_destination, local_file_path, s3_file_record_name)
            if upload_val is False:
                raise ValueError(f"FAILURE: file was not uploaded correctly -> bucket: {final_s3_bucket_destination}, file: {s3_file_record_name}")
            
            # delete object in temp bucket
            delete_val = delete(s3_bucket, s3_file_record_name)
            if delete_val is False:
                raise ValueError(f"FAILURE: file was not deleted correctly -> bucket: {s3_bucket}, file: {s3_file_record_name}")
               
            # delete local_file_path
            if os.path.isfile(local_file_path):
                os.remove(local_file_path)
        print(f"SUCCESS: Files tranferred from to {s3_bucket} to {final_s3_bucket_destination}")

        ### transfer record from temp to main file ledger ###
        # read in current document for file_id from temp file ledger - update #
        read_response = read(FILE_LEDGER_TEMP, "file_id", file_id)
        document = read_response[0]
        del document["file_id"]
        
        # update components of row
        document["status"]["receiver_end"] = "complete"
        document["file_metadata"]["s3_data"]["bucket_name"] = final_s3_bucket_destination
        update(FILE_LEDGER_TEMP, "file_id", file_id, document)
        print("SUCCESS: updated file ledger row on original ledger")

        # re-read
        read_response = read(FILE_LEDGER_TEMP, "file_id", file_id)
        row = read_response[0]
        del row["file_id"]

        # delete
        destroy(FILE_LEDGER_TEMP, "file_id", file_id)
        print("SUCCESS: deleted original row on temp ledger")

        # copy to main ledger
        create(final_file_ledger_destination, "file_id", file_id, row)
        print("SUCCESS: copied original row over to main file ledger")

        # uplaod finished file back to s3
        return {"statusCode": 200, "body": json.dumps({"user_id": user_id, "file_id": file_id, "request_id": request_id})}
    except Exception as e:
        # print failure message
        print(str(e))

        # report failure to history ledger
        document = {"request_id": request_id, "file_id": file_id, "user_id": user_id, "status_code": 500,  "lambda_function_name": LAMBDA_FUNCTION_NAME, "exception": str(e)}
        create(HISTORY_LEDGER_MAIN, "history_id", history_id, document)

        return {"statusCode": 500, "body": json.dumps({"request_id": request_id, "message": str(e)})}
