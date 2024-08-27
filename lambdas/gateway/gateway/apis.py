from gateway.gateway import api_gateway_client
from gateway.gateway.resources import get_all_resource_lambda_arns
from gateway.gateway.lambda_helpers import delete_api_resource_policies
import time


# list all apis
def list_apis():
    try:
        # list all apis
        response = api_gateway_client.get_rest_apis()

        # get all items
        apis = response["items"]

        # trim down each entry to id,name only
        apis = [{k: v for k, v in api.items() if k in ["id", "name"]} for api in apis]
        print("SUCCESS: list_apis succeeded")
        return apis
    except Exception as e:
        print(f"FAILURE: list_apis failed with exception {e}")
        raise e


# deploy api gateway staged endpoint
def deploy_api_endpoint(api_id: str, stage_name: str = "dev"):
    try:
        print(f"INFO: deploy_api_endpoint deploying API with id {api_id} to stage {stage_name}.")
        # Deploy the API to the specified stage
        api_gateway_client.create_deployment(restApiId=api_id, stageName=stage_name)
        print("SUCCESS: deploy_api_endpoint succeeded")
        return None
    except Exception as e:
        print(f"FAILURE: deploy_api_endpoint failed with exception {e}")
        return None


# create endpoint
def create_api_endpoint(api_name: str = "MyAPI", api_description: str = "My API Description") -> str:
    try:
        # check if api with api_name already exists
        # if it does, return api_id
        apis = list_apis()
        api_names = [api["name"] for api in apis]
        if api_name in api_names:
            api_id = apis[api_names.index(api_name)]["id"]
            print(f"API with name {api_name} already exists.")
            return api_id

        # Create the API
        api_response = api_gateway_client.create_rest_api(
            name=api_name,
            description=api_description,
            endpointConfiguration={"types": ["REGIONAL"]},
        )

        # Get the API ID
        api_id = api_response["id"]
        print(f"SUCCESS: create_api_endpoint creating API with name {api_name} and id {api_id}.")
        return api_id
    except Exception as e:
        print(f"FAILURE: create_api_endpoint failed with exception {e}")
        raise e


# delete api
def delete_api_endpoint(api_id: str) -> None:
    try:
        # deleting lambda policies assocated with api
        all_lambda_arns = get_all_resource_lambda_arns(api_id)

        for lambda_arn in all_lambda_arns:
            if lambda_arn is not None:
                print(f"lambda_arn: {lambda_arn}")
                delete_api_resource_policies(lambda_arn, api_id)

        print(f"SUCCESS: delete_api_endpoint deleted all lambda policies associated with api {api_id}.")
        time.sleep(1)

        # delete api
        response = api_gateway_client.delete_rest_api(restApiId=api_id)
        print(f"SUCCESS: delete_api_endpoint deleted API with id {api_id}.")
    except Exception as e:
        print(f"FAILURE: delete_api_endpoint deleting api with exception: {e}")
        raise e


def get_method_arns(api_id: str):
    try:
        # Get the resource for the specified path
        resource = api_gateway_client.get_resources(restApiId=api_id)

        # unpack items from resource
        items = resource["items"]

        # keep only items with resourceMethods key
        items = [item for item in items if "resourceMethods" in item.keys()]

        # lookup and store method arns
        all_method_arns = []
        if "items" in resource and len(resource["items"]) > 0:
            for i in range(len(items)):
                resource_id = items[i]["id"]

                # Specify the HTTP method you're interested in (e.g., GET, POST, etc.)
                http_method = "POST"

                # Get the method details, including the ARN
                method = api_gateway_client.get_method(restApiId=api_id, resourceId=resource_id, httpMethod=http_method)

                # Extract and print the ARN
                method_arn = method["methodIntegration"]["uri"]
                all_method_arns.append(method_arn)
        else:
            print(f"INFO: get_method_arns resource not found: {resource['path']}")
        print(f"SUCCESS: get_method_arns succeeded")
        return all_method_arns
    except Exception as e:
        print(f"FAILURE: get_method_arns failed with exception {e}")
        return None
