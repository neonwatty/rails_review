import os
import boto3
import io
from PIL import Image
import json
import requests


RAILS_DEVELOPMENT_HOST = os.environ["RAILS_DEVELOPMENT_HOST"]


def handler(event, context):
    # Process each record
    for record in event['Records']:
        processed_key = "processed_image.png"
        s3_bucket_name = "app-1-test"
        upload_id = 2

        data = {'s3_bucket_name': s3_bucket_name, 'processed_image_key': processed_key, 'upload_id': upload_id}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(RAILS_DEVELOPMENT_HOST, data=json.dumps(data), headers=headers)
    
        print(f"response --> {response}")

