from gateway.gateway.apis import create_api_endpoint, deploy_api_endpoint
from gateway.gateway.apis import delete_api_endpoint
from gateway.gateway.authorizer_helpers import create_authorizer
from gateway.gateway.resources import create_api_resource
from gateway.gateway import ACCOUNT_ID, STAGE, APP_NAME, GATEWAY_NUM
from tables.gateway.row_create import create as create_gateway_table
from tables.gateway.row_delete import delete as delete_gateway_table


def create() -> dict:
    try:
        # construct entrypoint arns
        input_entrypoint_lambda_arn = f"arn:aws:lambda:us-west-2:{ACCOUNT_ID}:function:entrypoints-{STAGE}-entrypoint_input"
        output_entrypoint_lambda_arn = f"arn:aws:lambda:us-west-2:{ACCOUNT_ID}:function:entrypoints-{STAGE}entrypoint_output"
        delete_entrypoint_lambda_arn = f"arn:aws:lambda:us-west-2:{ACCOUNT_ID}:function:entrypoints-{STAGE}entrypoint_delete"
        status_entrypoint_lambda_arn = f"arn:aws:lambda:us-west-2:{ACCOUNT_ID}:function:entrypoints-{STAGE}entrypoint_status"

        # define api_name
        api_name = f"{APP_NAME}-{GATEWAY_NUM}"

        # create api endpoint
        api_id = create_api_endpoint(api_name=api_name, api_description=f"app gateway number {GATEWAY_NUM}")

        # create authorizer
        authorizer_id = create_authorizer(api_id)

        ### create resource ids ###
        input_entrypoint_resource_id = create_api_resource(
            api_id=api_id,
            resource_name="entrypoint_input",
            lambda_arn=input_entrypoint_lambda_arn,
            authorizer_id=authorizer_id,
        )
        print(f"resource_name --> entrypoint_input, resource_id --> {input_entrypoint_resource_id}  ")

        output_entrypoint_resource_id = create_api_resource(
            api_id=api_id,
            resource_name="entrypoint_output",
            lambda_arn=output_entrypoint_lambda_arn,
            authorizer_id=authorizer_id,
        )
        print(f"resource_name --> entrypoint_output, resource_id --> {output_entrypoint_resource_id}  ")

        delete_entrypoint_resource_id = create_api_resource(
            api_id=api_id,
            resource_name="entrypoint_delete",
            lambda_arn=delete_entrypoint_lambda_arn,
            authorizer_id=authorizer_id,
        )
        print(f"resource_name --> entrypoint_delete, resource_id --> {delete_entrypoint_resource_id}  ")

        status_entrypoint_resource_id = create_api_resource(
            api_id=api_id,
            resource_name="entrypoint_status",
            lambda_arn=status_entrypoint_lambda_arn,
            authorizer_id=authorizer_id,
        )
        print(f"resource_name --> entrypoint_status, resource_id --> {status_entrypoint_resource_id}  ")

        # deploy api
        deploy_response = deploy_api_endpoint(api_id=api_id, stage_name=STAGE)

        # create resource / method arns of api
        # method_arns = get_method_arns(api_id=api_id)
        base_of_arn = f"arn:aws:execute-api:us-west-2:{ACCOUNT_ID}:"
        input_entrypoint_arn = f"{base_of_arn}{api_id}/*/POST/entrypoint_input"
        output_entrypoint_arn = f"{base_of_arn}{api_id}/*/POST/entrypoint_output"
        delete_entrypoint_arn = f"{base_of_arn}{api_id}/*/POST/entrypoint_delete"
        status_entrypoint_arn = f"{base_of_arn}{api_id}/*/POST/entrypoint_status"

        resource_arns = []
        resource_arns.append(input_entrypoint_arn)
        resource_arns.append(output_entrypoint_arn)
        resource_arns.append(delete_entrypoint_arn)
        resource_arns.append(status_entrypoint_arn)

        # update apigateway_table api_id row with user_id
        create_gateway_table(
            api_id=api_id,
            resource_arns=resource_arns,
        )

    except Exception as e:
        delete_val = delete_api_endpoint(api_id)
        delete_gateway_table(api_id)
        raise e


if __name__ == "__main__":
    create()
