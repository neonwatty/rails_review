from functools import wraps
from receivers .utilities.setup_teardown import setup, teardown


def receiver_setup_teardown(local_input_ext, local_output_ext):
    def decorator(func):
        @wraps(func)
        def wrapper(event, context):
            # draft setup payload and load data to lambda
            setup_payload = setup(event, local_input_ext, local_output_ext)
            
            # call receiver function
            result = func(event, context)
            
            # teardown and wrapup
            teardown_val = teardown(setup_payload)

            return result
        return wrapper
    return decorator        
  