from functools import wraps
from receivers .utilities.setup_teardown import setup, teardown


def receiver_setup_teardown(local_input_ext, local_output_ext):
    def decorator(func):
        @wraps(func)
        def wrapper(event, context):
            # draft setup payload and load data to lambda
            setup_payload = setup(event, local_input_ext, local_output_ext)
            
            # pass data from setup_payload to event for receiver function
            event["local_input_path"] = setup_payload["local_input_path"]
            event["local_output_path"] = setup_payload["local_output_path"]
            event["receiver_name"] = setup_payload["receiver_name"]
            event["user_id"] = setup_payload["user_id"]
            event["upload_id"] = setup_payload["upload_id"]
            
            # call receiver function
            result = func(event, context)
            
            # teardown and wrapup
            teardown_val = teardown(setup_payload)

            return result
        return wrapper
    return decorator        
  