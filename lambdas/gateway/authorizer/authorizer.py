from tables.gateway.row_read import read as gateway_read
from tables.secrets.row_read import read_api_key as secrets_api_key_read


def generate_final_policy(principal_id: str, auth: str, method_arns: list):
    policy_document = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": auth,
                    "Resource": method_arns,
                }
            ],
        },
    }
    return policy_document


# Main lambda function
def handler(event, context):
    # assert methodArn in event and is not None
    assert "methodArn" in event, "methodArn not in event"
    assert event["methodArn"] is not None, "methodArn is None"

    # assert authorizationToken is in event and is not None
    assert "authorizationToken" in event, "authorizationToken not in event"
    assert event["authorizationToken"] is not None, "authorizationToken is None"

    # init auth
    auth = "Deny"

    # unpack methodArn event
    methodArn = event["methodArn"]

    # parse methodArn for api_id
    api_id = methodArn.split(":")[-1].split("/")[0]

    # unpack authorizationToken event
    api_key = event["authorizationToken"]

    try:
        # lookup user_id from api_key
        response = secrets_api_key_read(api_key)
        user_id = response.get("user_id", None)
        assert user_id is not None, "FAILURE: user_id not found from api_key"

        # lookup user_id from apigateway_table given api_id
        response = gateway_read(api_id)

        # retrieve resource_arns
        resource_arns = response["Item"]["resource_arns"]

        # generate policy document
        auth = "Allow"
        policy_document = generate_final_policy(api_key, auth, resource_arns)
        return policy_document
    except Exception as e:
        print(f"FAILURE: authorizer failed with exception {e}")
        # generate policy document
        auth = "Deny"
        policy_document = generate_final_policy(api_key, auth, [])
        return policy_document
