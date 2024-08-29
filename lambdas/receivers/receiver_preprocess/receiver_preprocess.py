import os
import json
import boto3
from PIL import Image
import io

from receivers import s3_client
from sqs.messages.message_create import message_create
from decorators.warmer import warmer
from decorators.message import sqs_receiver_wrapper
from receivers.utilities.create_io_dir import local_input_file_path, local_output_file_path

STAGE = os.environ["STAGE"]
APP_NAME = os.environ["APP_NAME"]

STATUS_QUEUE = f"{APP_NAME}-test-status"
BUCKET_NAME_SAVE = f"{APP_NAME}-test"
if STAGE in ["development", "production"]:
    STATUS_QUEUE = f"{APP_NAME}-status"
    BUCKET_NAME_SAVE = f"{APP_NAME}-trigger"


@warmer
@sqs_receiver_wrapper
def lambda_handler(event, context):
    # unpack required objects from event
    s3_bucket = event["s3"]["bucket"]["name"]
    s3_key = event["s3"]["object"]["key"]

    # deconstruct s3_key into stage, user_id, file_id, and file_name
    s3_key_split = s3_key.split("/")
    user_id = s3_key_split[0]
    upload_id = s3_key_split[1]
    file_name = s3_key_split[2]

    # try function
    try:            
        # Download the image from S3
        s3_client.download_file(s3_bucket, s3_key, local_input_file_path)
        
        # Open the image using Pillow
        image = Image.open(local_input_file_path)
        
        # Resize the image
        new_size = (800, 600)  # Desired size
        resized_image = image.resize(new_size)

        # Save the processed image to the specified output file path
        resized_image.save(local_output_file_path)
        
        # upload file
        s3_key_save = f"{user_id}/{upload_id}/receiver_preprocess"
        s3_client.upload_file(local_output_file_path, s3_bucket, s3_key_save)
        
        # send status update to queue
        status = {
            "url": "status_update",
            "lambda": "receiver_preprocess",
            "user_id": user_id,
            "upload_id": upload_id,
            "status": "complete"
        }
        
        response = message_create(STATUS_QUEUE, status)
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            success_message = "SUCCESS: receiver_start executed successfully"
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'success', 'message': success_message, "s3_key_save":s3_key_save, "bucket_name_save": BUCKET_NAME_SAVE})
            }

        # uplaod finished file back to s3
        return {"statusCode": 200, "body": json.dumps({"s3_key_save": s3_key_save, "bucket_name_save": BUCKET_NAME_SAVE})}
    except Exception as e:
        try:
            # send status update to queue   
            status = {
                "url": "status_update",
                "lambda": "receiver_preprocess",
                "user_id": user_id,
                "upload_id": upload_id,
                "status": "fail"
            }
            response = message_create(STATUS_QUEUE, status)
        except:
            pass
        
        # print failure message
        failure_message = str(e)
        print(failure_message)

        return {"statusCode": 500, "body": json.dumps({"message": failure_message})}