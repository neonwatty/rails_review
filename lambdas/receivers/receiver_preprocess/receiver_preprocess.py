from PIL import Image
from decorators.warmer import warmer
from decorators.receiver import receiver_decorator


@warmer
@receiver_decorator(local_input_ext=".jpg", local_output_ext=".jpg")
def lambda_handler(event, context):
    try:
        # Open the image using Pillow
        image = Image.open(event["local_input_path"])

        # convert
        image = image.convert("RGB")

        # Resize the image
        new_size = (800, 600)  # Desired size
        resized_image = image.resize(new_size)

        # Save the processed image to the specified output file path
        resized_image.save(event["local_output_path"])

        # return
        message = f"SUCCESS: receiver for {event["receiver_name"]} ran successfully"
        print(message)
        return {"statusCode": 200, "body": {"receiver_name": event["receiver_name"], "message": message}}
    except Exception as e:
        message = f"FAILURE: receiver for {event["receiver_name"]} failed with exception {str(e)}"
        print(message)
        return {"statusCode": 500, "body": {"receiver_name": event["receiver_name"], "message": message}}
