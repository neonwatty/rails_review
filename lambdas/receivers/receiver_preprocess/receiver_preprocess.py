import json
from PIL import Image
from sqs.messages.message_create import message_create
from decorators.warmer import warmer
from decorators.message import sqs_receiver_wrapper, sqs_status_wrapper
from decorators.receiver import receiver_setup_teardown


@warmer
@sqs_status_wrapper
@receiver_setup_teardown(local_input_ext=".jpg", local_output_ext=".jpg")
@sqs_receiver_wrapper
def lambda_handler(event, context):    
    try:        
        # Open the image using Pillow
        image = Image.open(event["local_input_path"])
        
        # Resize the image
        new_size = (800, 600)  # Desired size
        resized_image = image.resize(new_size)

        # Save the processed image to the specified output file path
        resized_image.save(event["local_output_path"])
        
        # return 
        message = f"SUCCESS: receiver for {event["receiver_name"]} ran successfully"
        print(message)
        return {
            "statusCode": 200,  "body": json.dumps({"message": message})
        }
    except Exception as e:
        message = f"FAILURE: receiver for {event["receiver_name"]} failed with exception {str(e)}"
        print(message)
        return {"statusCode": 500, "body": json.dumps({"message": message})}