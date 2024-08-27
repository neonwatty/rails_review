from gateway.gateway import api_gateway_client
from gateway.gateway import ACCOUNT_ID, STAGE, AUTHORIZER_NAME
from typing import Tuple


def check_if_authorizer_exists(api_id: str, check_name: str) -> Tuple[bool, str]:
    try:
        # list all api authorizers
        authorizers = api_gateway_client.get_authorizers(restApiId=api_id)

        # extract all authorizer names
        authorizer_names = [authorizer["name"] for authorizer in authorizers["items"]]

        # find index of check_name in authorizer_names
        check_index = -1
        if check_name in authorizer_names:
            check_index = authorizer_names.index(check_name)

        # if check_index is -1, then check_name does not exist
        if check_index == -1:
            print(f"INFO: check_if_authorizer_exists failed because check_name {check_name} not in authorizer_names {authorizer_names}")
            return False, ""
        else:
            # find id of check_index element of authorizers
            authorizer_id = authorizers["items"][check_index]["id"]
            print("SUCCESS: check_if_authorizer_exists succeeded")
            return True, authorizer_id
    except Exception as e:
        print(f"FAILURE: check_if_authorizer_exists failed with exception {e}")
        return False, ""


def create_authorizer(api_id: str) -> str:
    try:
        # Name for the authorizer
        authorizer_name = "app_authorizer"

        # check if authorizer already exists
        check_val, check_id = check_if_authorizer_exists(api_id, authorizer_name)
        if check_val:
            return check_id

        # ARN of the Lambda function
        lambda_arn = f"arn:aws:lambda:us-west-2:{ACCOUNT_ID}:function:{AUTHORIZER_NAME}-{STAGE}-handler"
        authorizer_arn = f"arn:aws:apigateway:us-west-2:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        authorizer_credentials = f"arn:aws:iam::{ACCOUNT_ID}:role/APIGatewayInvokeLambdaRole"

        # create authorizer
        authorizer = api_gateway_client.create_authorizer(
            restApiId=api_id,
            name=authorizer_name,
            type="TOKEN",
            authorizerUri=authorizer_arn,
            authorizerCredentials=authorizer_credentials,
            identitySource="method.request.header.appApiKey",
            authorizerResultTtlInSeconds=300,
        )

        # return authorizer id
        authorizer_id = authorizer["id"]
        print(f"SUCCESS: create_authorizer succeded with {authorizer_id}")
        return authorizer_id
    except Exception as e:
        print(f"FAILURE: create_authorizer failed with exception {e}")
        raise e


def delete_all_api_authorizers(api_id: str):
    try:
        authorizers = api_gateway_client.get_authorizers(restApiId=api_id)
        for authorizer in authorizers["items"]:
            authorizer_id = authorizer["id"]
            api_gateway_client.delete_authorizer(restApiId=api_id, authorizerId=authorizer_id)
        print("SUCCESS: delete_all_api_authorizers succeeded")
        return True
    except Exception as e:
        print(f"FAILURE: delete_all_api_authorizers failed with exception {e}")
        return False
