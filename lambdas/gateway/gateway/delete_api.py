from gateway.gateway.apis import delete_api_endpoint
from tables.gateway.row_delete import delete as gateway_row_delete
from tables.secrets.row_delete import delete as secrets_row_delete
from tables.secrets.row_read import read_gsi as secrets_read_gsi


def delete(api_id: str):
    # if len(sys.argv) < 2:
    #     print("Usage: python delete_api.py <api_id>")
    #     sys.exit(1)

    # # Retrieve the first command-line argument
    # api_id = sys.argv[1]

    try:
        # delete api and all associated lambda policies
        delete_api_endpoint(api_id)

        # update user_id secrets table to remove api_id
        response = secrets_read_gsi(api_id=api_id)
        items = response.get("Items") or response.get("Item") or []
        if len(items) > 0:
            for item in items:
                user_id = item["user_id"]
                secrets_row_delete(user_id)

        # delete row from apigateway_table
        gateway_row_delete(api_id=api_id)

        return {"statusCode": 200, "body": f"Deleted API with id {api_id}."}
    except Exception as e:
        failure_message = f"FAILURE: delete api failed on api_id {api_id} with exception {e}."
        print(failure_message)
        return {"statusCode": 500, "body": failure_message}


if __name__ == "__main__":
    delete()
