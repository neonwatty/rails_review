import os
import json
from PIL import Image
from sqs.messages.message_create import message_create
from decorators.warmer import warmer
from decorators.message import sqs_receiver_wrapper, sqs_status_wrapper
from decorators.receiver_setup_teardown import 


BUCKET_NAME_SAVE = f"{APP_NAME}-test"



    


@warmer
@sqs_receiver_wrapper
def lambda_handler(event, context):    
    # run setup
    setup_payload = setup(event, local_input_ext=".jpg", local_output_ext=".jpg")

    try:        
        # Open the image using Pillow
        image = Image.open(setup_payload["local_input_path"])
        
        # Resize the image
        new_size = (800, 600)  # Desired size
        resized_image = image.resize(new_size)

        # Save the processed image to the specified output file path
        resized_image.save(setup_payload["local_output_path"])
        
        # wrapup
        return wrapup(setup_payload, receiver_name="receiver_process")
    except Exception as e:
        try:

        except:
            pass
        
        # print failure message
        failure_message = str(e)
        print(failure_message)

        return {"statusCode": 500, "body": json.dumps({"message": failure_message})}