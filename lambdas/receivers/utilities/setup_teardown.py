import os
from receivers import s3_client
from receivers.utilities.create_io_dir import local_input_file_path, local_output_file_path


def setup(event: dict, local_input_ext: str | None = None, local_output_ext: str | None = None) -> dict | None:
    try:
        # unpack required objects from event
        s3_bucket = event["s3"]["bucket"]["name"]
        s3_key = event["s3"]["object"]["key"]

        # deconstruct s3_key into stage, user_id, file_id, and file_name
        s3_key_split = s3_key.split("/")
        user_id = s3_key_split[0]
        upload_id = s3_key_split[1]
        receiver_name = s3_key_split[2]
        
        # adjust local_input_file_path for function to work properly
        local_input_path = local_input_file_path + local_input_ext if local_input_ext is not None else local_input_file_path
        local_output_path = local_output_file_path + local_output_ext if local_output_ext is not None else local_output_file_path
            
        # Download the image from S3
        s3_client.download_file(s3_bucket, s3_key, local_input_path)
        
        # return setup payload
        setup_payload = {}
        setup_payload["user_id"] = user_id
        setup_payload["upload_id"] = upload_id
        setup_payload["local_input_path"] = local_input_path
        setup_payload["local_output_path"] = local_output_path
        setup_payload["s3_bucket"] = s3_bucket
        setup_payload["s3_key"] = s3_key
        setup_payload["receiver_name"] = receiver_name
        return setup_payload
    except Exception as e:
        failure_message = f"FAILURE: setup for receiver {receiver_name} failed with exception {str(e)}"
        print(failure_message)
        return None
  
    
def teardown(setup_payload: dict) -> bool:
  try:
      # upload file
      s3_key_save = f"{setup_payload["user_id"]}/{setup_payload["upload_id"]}/{setup_payload["receiver_name"]}"
      s3_client.upload_file(setup_payload["local_output_path"], setup_payload["s3_bucket"], s3_key_save)
      return True
  except Exception as e:
      failure_message = f"FAILURE: teardown for receiver {setup_payload["receiver_name"]} failed with exception {str(e)}"
      print(failure_message)
      return False