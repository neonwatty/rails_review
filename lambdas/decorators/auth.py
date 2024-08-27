import json
import functools
import uuid
from tables.secrets.row_read import read_api_key


def auth_confirm(func):
    @functools.wraps(func)
    def wrapper(event, context):
        # generate request_id
        request_id = str(uuid.uuid4())
        try:
            if "headers" not in event:
                raise KeyError("FAILURE: 'headers' not found in event")
            headers = event["headers"]
            if "appApiKey" not in headers:
                raise KeyError("FAILURE: 'appApiKey' not found in headers")
            api_key = headers["appApiKey"]
            if api_key is None:
                raise ValueError("FAILURE: 'api_key' is None")

            # unpack ids
            response = read_api_key(api_key)
            user_id = response.get("user_id", None)

            # if user_id is None, return failure
            if user_id is None:
                raise ValueError("FAILURE: 'user_id' is None")

            # add user_id and request_id to event
            event["user_id"] = user_id
            event["request_id"] = request_id

            # return func
            print("SUCCESS: auth_confirm successful")

            return func(event, context)
        except Exception as e:
            print(str(e))
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "message": str(e),
                        "request_id": request_id,
                        "items": [],
                        "warnings": [],
                    }
                ),
            }
    return wrapper
