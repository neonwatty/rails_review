import json
import random
import string
from gateway.gateway import lambda_client


def generate_alpha_numeric_sid():
    try:
        # Define a pool of characters consisting of letters (both cases) and numbers
        characters = string.ascii_letters + string.digits

        # Use random.choices to generate a SID with a UUID-like format
        sid = (
            "".join(random.choices(characters, k=8))
            + "-"
            + "".join(random.choices(characters, k=4))
            + "-"
            + "".join(random.choices(characters, k=4))
            + "-"
            + "".join(random.choices(characters, k=4))
            + "-"
            + "".join(random.choices(characters, k=12))
        )
        print("SUCCESS: generate_alpha_numeric_sid succeeded")
        return sid
    except Exception as e:
        print(f"FAILURE: generate_alpha_numeric_sid failed with exception {e}")
        return None


def attach_resource_policy(lambda_arn: str, method_execution_arn: str, policy_name: str):
    try:
        response = lambda_client.add_permission(
            Action="lambda:InvokeFunction",
            FunctionName=lambda_arn,
            Principal="apigateway.amazonaws.com",
            SourceArn=method_execution_arn,
            StatementId=policy_name,  # generate_alpha_numeric_sid()
        )
        print("SUCCESS: attach_resource_policy succeeded")
        return response
    except Exception as e:
        print(f"FAILURE: attach_resource_policy failed with exception {e}")


def delete_api_resource_policies(lambda_arn: str, api_id: str):
    try:
        # get all permissions for lambda
        response = lambda_client.get_policy(FunctionName=lambda_arn)

        # remove all permissions with statement_id beginning with api_id
        for statement in json.loads(response["Policy"])["Statement"]:
            if statement["Sid"].split("-")[0] == api_id:
                response = lambda_client.remove_permission(FunctionName=lambda_arn, StatementId=statement["Sid"])

        print(
            f"SUCCESS: delete_api_resource_policies succeeded and all permissions for lambda {lambda_arn} with statement_id beginning with {api_id}."
        )
    except Exception as e:
        print(
            f"FAILURE: delete_api_resource_policies failed to remove all permissions for lambda {lambda_arn} with statement_id beginning with {api_id}."
        )
        print(e)
