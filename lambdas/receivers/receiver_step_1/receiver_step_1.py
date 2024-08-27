import os
import json
import uuid
from receivers import s3_client
from decorators.warmer import warmer
from decorators.message import sqs_receiver_wrapper
from receivers.utilities.create_io_dir import local_input_file_path, local_output_path
from tables.public.row_update import update
from tables.public.row_create import create
from tables.public.row_read import read


STAGE = os.environ.get("STAGE", "dev")
FILE_LEDGER_TEMP = os.environ["FILE_LEDGER_TEMP"]
HISTORY_LEDGER_MAIN = os.environ["HISTORY_LEDGER_MAIN"]
LAMBDA_FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "local-test")
KRIXIK_URL = os.environ["KRIXIK_URL"]
KRIXIK_KEY = os.environ["KRIXIK_KEY"]

from krixik import krixik
krixik.init(api_key=KRIXIK_KEY, api_url=KRIXIK_URL)

# create a pipeline with a single transcribe module
pipeline = krixik.create_pipeline(name="yt_shorts_transcribe_app", module_chain=["transcribe"])


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
        # download file to lambda
        s3_client.download_file(s3_bucket, s3_key, local_input_file_path + ".mp3") # required extension by app
        print(f"SUCCESS: File downloaded to {local_input_file_path}.mp3")
        
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
        receiver_progress = read_status["receiver_step_1"]
                
        # if receiver_process already complete, return
        if receiver_progress == "complete" or receiver_progress == "in progress":
            return {"statusCode": 400, "body": json.dumps({"request_id": request_id, "message": "FAILURE: file with file_id already exists"})}

        # if receiver_process failed, add entry to history table for scheduled deletion
        if receiver_progress == "fail":  # SHOULD WE FAIL OUT HERE OR RE-TRY?
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
        print("SUCCESS: file file_id passed inspection")
        
        # set receiver_step_1 to "in progress" TODO
        read_status["receiver_step_1"] = "in progress"
        update_document = {"status": read_status}
        update(FILE_LEDGER_TEMP, "file_id", file_id, update_document)
        
        
        # delete previous run's result
        list_response = pipeline.list(file_names=["yt_shorts_transcription_app.mp3"])
        list_items = list_response["items"]
        if len(list_items) > 0:
            for item in list_items:
                krixik_file_id = item["file_id"]
                delete_result = pipeline.delete(file_id=krixik_file_id)
                assert delete_result["status_code"] == 200
        
        # process the file with the default model
        process_output = pipeline.process(
            local_file_path=local_input_file_path + ".mp3",
            local_save_directory=local_output_path,
            expire_time=60 * 30, 
            wait_for_process=True,
            verbose=False,
            file_name="yt_shorts_transcription_app.mp3",
            modules={"transcribe": {"model": "whisper-base"}}
        ) 

        # krixik file id
        krixik_file_id = process_output["file_id"]
        print(f"process output from krixik --> {process_output}")
                
        # load in process output from file - here we only print the transcript, and not the timestamped version, since the output is quite long
        transcript = process_output["process_output"][0]
        print(f"transcript --> {transcript}")
                
        # save file back to s3
        s3_key_save = f"{STAGE}/{user_id}/{file_id}/receiver_step_1.json"
        krixik_file_output_path = local_output_path + "/" + f"{krixik_file_id}.json"
        s3_client.upload_file(krixik_file_output_path, s3_bucket, s3_key_save)
        
        # delete file on krixik server
        krixik_delete_result = pipeline.delete(file_id=krixik_file_id)
        assert krixik_delete_result["status_code"] == 200

        # read in current document for file_id from temp file ledger
        read_response = read(FILE_LEDGER_TEMP, "file_id", file_id)
        document = read_response[0]
        del document["file_id"]

        document["status"]["receiver_step_1"] = "complete"
        document["file_metadata"]["s3_data"]["files"]["receiver_step_1"] = s3_key_save
        document["transcript"] = transcript
                
        update(FILE_LEDGER_TEMP, "file_id", file_id, document)
        
        print(f"SUCCESS: step 1 process completed successfully")

        # uplaod finished file back to s3
        return {"statusCode": 200, "body": json.dumps({"s3_key_save": s3_key_save, "user_id": user_id, "file_id": file_id, "request_id": request_id})}
    except Exception as e:
        # print failure message
        print(str(e))

        # report failure to history ledger
        document = {"request_id": request_id, "file_id": file_id, "user_id": user_id, "status_code": 500,  "lambda_function_name": LAMBDA_FUNCTION_NAME, "exception": str(e)}
        create(HISTORY_LEDGER_MAIN, "history_id", history_id, document)

        return {"statusCode": 500, "body": json.dumps({"request_id": request_id, "message": str(e)})}