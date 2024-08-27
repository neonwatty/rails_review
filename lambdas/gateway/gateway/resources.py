import time
from gateway.gateway import api_gateway_client
from gateway.gateway.lambda_helpers import attach_resource_policy
from gateway.gateway import ACCOUNT_ID
import sys


# get resources associated with an api
def get_api_resources(api_id: str):
    try:
        # get resources id of api_id
        response = api_gateway_client.get_resources(restApiId=api_id.split(":")[-1])

        # unpack items
        items = response["items"]
        print("SUCCESS: get_api_resources succeeded")
        return items
    except Exception as e:
        print(f"FAILURE: get_api_resources failed with exception {e}")
        return None


# filter just for root id
def root_id_filter(items: list):
    try:
        # keep only items that do not have parent id
        items = [item for item in items if "parentId" not in item.keys()]

        # get root resource id
        root_resource_id = items[-1]["id"]
        print("SUCCESS: root_id_filter succeeded")
        return root_resource_id
    except Exception as e:
        print(f"FAILURE: root_id_filter failed with exception {e}")
        return None


# filter for non-root ids
def non_root_filter(items: list):
    try:
        # keep only items that do not have parent id
        items = [item for item in items if "parentId" in item.keys()]
        print("SUCCESS: non_root_filter succeeded")
        return items
    except Exception as e:
        print(f"FAILURE: non_root_filter failed with exception {e}")


# check if non-root resource exists by name
def check_if_non_root_resource_exists(api_id: str, resource_name: str):
    try:
        # get resources id of api_id
        items = get_api_resources(api_id)

        # keep only non-root items
        items = non_root_filter(items)

        # check if resource_name exists
        resource_exists = resource_name in [item["pathPart"] for item in items]

        # if resource exists, get id of resource_name
        print("SUCCESS: check_if_non_root_resource_exists succeeded")
        if resource_exists:
            resource_id = [item["id"] for item in items if item["pathPart"] == resource_name][0]
            return resource_exists, resource_id
        else:
            return resource_exists, None
    except Exception as e:
        print(f"FAILURE: check_if_non_root_resource_exists failed with exception {e}")
        return None, None


# get root resource id for an input api id
def get_root_resource_id(api_id: str):
    try:
        # get resources id of api_id
        items = get_api_resources(api_id)

        # filter for root id
        root_resource_id = root_id_filter(items)
        print("SUCCESS: get_root_resource_id succeeded")
        return root_resource_id
    except Exception as e:
        print(f"FAILURE: get_root_resource_id failed with exception {e}")
        return None


# delete resource
def delete_resource_by_name(api_id: str, resource_name: str):
    try:
        # get resources id of api_id
        items = get_api_resources(api_id)

        # check if resource_name exists
        resource_exists = resource_name in [item["pathPart"] for item in items]

        if resource_exists:
            # get resource id
            resource_id = [item["id"] for item in items if item["pathPart"] == resource_name][0]

            # delete resource
            response = api_gateway_client.delete_resource(restApiId=api_id, resourceId=resource_id)
            print(f"SUCCESS: delete_resource_by_name succeeded and deleted resource with name {resource_name}.")
            return response
        else:
            print(f"SUCCESS: resource with name {resource_name} does not exist.")
            return None
    except Exception as e:
        print(f"FAILURE: delete_resource_by_name failed with exception {e}")
        return None


# delete resource by id
def delete_resource_by_id(api_id: str, resource_id: str):
    try:
        # get resources id of api_id
        items = get_api_resources(api_id)

        # check if resource_name exists
        resource_exists = resource_id in [item["id"] for item in items]

        if resource_exists:
            # delete resource
            response = api_gateway_client.delete_resource(restApiId=api_id, resourceId=resource_id)
            print(f"SUCCESS: delete_resource_by_id succeeded and deleted resource with id {resource_id}.")
            return response
        else:
            print(f"SUCCESS: succeeded but resource with id {resource_id} does not exist.")
            return None
    except Exception as e:
        print(f"FAILURE: delete_resource_by_id failed with exception {e}")
        return None


# add resource to api
def add_resource_to_api(api_id: str, resource_name: str):
    try:
        role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/APIGatewayInvokeLambdaRole"

        # check if resource with resource_name already exists
        resource_exists, resource_id = check_if_non_root_resource_exists(api_id, resource_name)
        if resource_exists:
            print(f"Resource with name {resource_name} already exists.")
            return resource_id

        ## otherwise, create resource
        # get root resource id of api_id
        root_resource_id = get_root_resource_id(api_id)

        # try to create resource
        if root_resource_id is not None:
            print(f"INFO: creating resource with name {resource_name}.")
            # if root resource id exists, create child resource
            resource_response = api_gateway_client.create_resource(restApiId=api_id, parentId=root_resource_id, pathPart=resource_name)
            print("INFO: ...done!")

            # get new resource id
            resource_id = resource_response["id"]
            print(f"SUCCESS: add_resource_to_api succeeded")
            return resource_id
        else:
            print(f"FAILURE: add_resource_to_api failed and could not create resource with name {resource_name}.")
            return None
    except Exception as e:
        print(f"FAILURE: add_resource_to_api failed with exception {e}")
        return None


# get lambda arn associated with a resource
def get_resource_lambda(api_id: str, resource_id: str):
    try:
        print(f"INFO: starting get_resource_lambda for api_id {api_id} and resource_id {resource_id}")
        response = api_gateway_client.get_method(restApiId=api_id, resourceId=resource_id, httpMethod="POST")

        # Get the Lambda function ARN from the method's integration
        method_integration = response["methodIntegration"]
        lambda_arn = method_integration["uri"]
        lambda_arn = lambda_arn.split("/")[-2]
        print("SUCCESS: get_resource_lambda succeeded")
        return lambda_arn
    except Exception as e:
        print(f"FAILURE: get_resource_lambda failed with exception {e}")
        return None


# get resource methods
def get_resource_methods(api_id: str, resource_id: str):
    try:
        # get methods for resource
        response = api_gateway_client.get_resource(restApiId=api_id, resourceId=resource_id)

        # get methods
        methods = {"id": response["id"], "resourceMethods": response["resourceMethods"]}

        # get method items
        # method_items = [{'httpMethod': http_method} for http_method in methods.keys()]
        print("SUCCESS: get_resource_methods succeeded")
        return methods
    except Exception as e:
        print(f"FAILURE: get_resource_methods failed with exception {e}")
        return None


def check_if_method_exists(api_id: str, resource_id: str, http_method: str):
    try:
        # get methods for resource
        method_items = get_resource_methods(api_id, resource_id)
        method_data = None

        # check if method exists
        if method_items is not None:
            method_exists = http_method in method_items["resourceMethods"].keys()
        else:
            method_exists = False

        if method_exists:
            # get method_data associted with http_method
            method_data = [method for method in method_items if http_method in method_items["resourceMethods"].keys()][0]
        print("SUCCESS: check_if_method_exists succeeded")
        return method_exists, method_data
    except Exception as e:
        print(f"FAILURE: check_if_method_exists failed with exception {e}")
        return None, None


# add method to resource
def add_method_to_resource(
    api_id: str,
    resource_id: str,
    http_method: str,
    authorization_type: str,
    authorizer_id: str,
):
    try:
        # check if method with http_method already exists
        method_exists, method_data = check_if_method_exists(api_id, resource_id, http_method)
        if method_exists:
            print(f"INFO: add_method_to_resource method with http method {http_method} already exists.")
            return method_data

        # Create a method for input resource
        print(f"INFO: add_method_to_resource creating method with http method {http_method} for resource with id {resource_id}.")
        method_response = api_gateway_client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            authorizationType=authorization_type,
            authorizerId=authorizer_id,
        )
        print("SUCCESS: add_method_to_resource succeeded")
        return method_response
    except Exception as e:
        print(f"FAILURE: add_method_to_resource failed with exception {e}")
        return None


def add_lambda_integration_to_resource_method(
    api_id: str,
    resource_id: str,
    http_method: str,
    lambda_arn: str,
    integration_type: str = "AWS_PROXY",
):
    try:
        # formulate method arn from lambda arn
        method_arn = f"arn:aws:apigateway:us-west-2:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"

        # Add integration for method
        integration_response = api_gateway_client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type=integration_type,
            uri=method_arn,
            integrationHttpMethod=http_method,
            # credentials=role_arn
        )
        print(f"SUCCESS: add_lambda_integration_to_resource_method added lambda integration to resource method with http method {http_method}.")

        return integration_response
    except Exception as e:
        print(f"FAILURE: add_lambda_integration_to_resource_method failed with exception {e}")
        return None


def get_all_resource_lambda_arns(api_id: str):
    try:
        # list all resource_ids associated with an input api_id
        all_resources = get_api_resources(api_id)
        print(f"INFO: all_resources --> {all_resources}")
        non_root_resources = non_root_filter(all_resources)

        # get all resource ids
        all_resource_ids = [resource["id"] for resource in all_resources]

        # get all lambda arns associated with an input api_id and resource_id
        all_lambda_arns = []
        for resource_id in all_resource_ids:
            lambda_arn = get_resource_lambda(api_id, resource_id)
            if lambda_arn is not None:
                all_lambda_arns.append(lambda_arn)
        print("SUCCESS: get_all_resource_lambda_arns succeeded")
        return all_lambda_arns
    except Exception as e:
        print(f"FAILURE: get_all_resource_lambda_arns failed with exception {e}")
        return None


def create_api_resource(api_id: str, resource_name: str, lambda_arn: str, authorizer_id: str):
    try:
        print(f"INFO: creating resource_id for resource_name {resource_name}")
        # add resource to api
        resource_id = add_resource_to_api(api_id=api_id, resource_name=resource_name)
        print(f"INFO:...done!  resource_id = {resource_id}")

        time.sleep(1)

        # add method to resource
        print(f"INFO: adding method to resource_id {resource_id}")
        http_method = "POST"  # note: this must be set to POST when using lambda integrations
        authorization_type = "CUSTOM"
        method_response = add_method_to_resource(
            api_id=api_id,
            resource_id=resource_id,
            http_method=http_method,
            authorization_type=authorization_type,
            authorizer_id=authorizer_id,
        )
        time.sleep(1)

        # create and attach  policy document to target lambda function
        print(f"INFO: attach_resource_policy to lambda_arn {lambda_arn}")

        method_execution_arn = f"arn:aws:execute-api:us-west-2:{ACCOUNT_ID}:{api_id}/*/{http_method}/{resource_name}"
        policy_name = f"{api_id}-{resource_name}-{http_method}-policy"
        policy_response = attach_resource_policy(lambda_arn, method_execution_arn, policy_name)
        time.sleep(1)

        # add lambda integration to resource method
        integration_response = add_lambda_integration_to_resource_method(
            api_id=api_id,
            resource_id=resource_id,
            http_method=http_method,
            lambda_arn=lambda_arn,
            integration_type="AWS_PROXY",
        )
        time.sleep(1)
        return resource_id
    except Exception as e:
        print(e)
        raise e
