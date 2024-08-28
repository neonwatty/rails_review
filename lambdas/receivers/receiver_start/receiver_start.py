import os
import json
from receivers import s3_client
from decorators.warmer import warmer
from tables.public.row_update import update
from tables.public.row_read import read
from receivers.utilities.create_io_dir import local_input_file_path, local_output_file_path

BUCKET_TEST = os.environ["BUCKET_TEST"]
BUCKET_TRIGGER = os.environ["BUCKET_TRIGGER"]


@warmer
def lambda_handler(event, context):
    try:
        # print event for testing
        print(f"event -> {event}")
        
        # Parse the JSON payload
        message = event["message"]
        file_key = event["file_key"]
        bucket_name = event["bucket_name"]
        stage = event["stage"]
        user_id = event["user_id"]
        upload_id = event["upload_id"]
        
        # route file copy to appropriate bucket based on stage
        bucket_name_save = BUCKET_TEST
        if stage == "test":
            pass
        if stage == "development":
            pass
        if stage == "production": 
            pass
        
        # download file to lambda
        s3_client.download_file(bucket_name, file_key, local_input_file_path)
        print(f"SUCCESS: File downloaded to {local_input_file_path}")
        
        # save file back to s3
        s3_key_save = f"{stage}-{user_id}-{upload_id}-entrypoint_input"
        s3_client.upload_file(local_output_file_path, bucket_name_save, s3_key_save)
        print("SUCCESS: Audio uploaded to s3")

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'success', 'message': message})
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Invalid JSON payload'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }