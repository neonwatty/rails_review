import json
from aws import session
from botocore.exceptions import ClientError

sqs_client = session.client("sqs")


def get_queue_url(queue_name:str) -> str | None:
    try:
        response = sqs_client.get_queue_url(QueueName=queue_name)
        return response.get('QueueUrl')
    except ClientError as e:
        print(f"FAILURE: ClientError: {e}")
        return None
    except Exception as e:
        print(f"FAILURE: An error occurred: {e}")
        return None

def attach_policy_to_sqs_queue(queue_name: str, account_id: str, bucket_name: str):
    # Get the queue URL
    queue_url = get_queue_url(queue_name)
    if not queue_url:
        print(f"Failed to retrieve URL for queue '{queue_name}'.")
        return

    # Define the policy template
    policy_template = {
        "Sid": "S3 connection",
        "Effect": "Allow",
        "Principal": {
            "Service": "s3.amazonaws.com"
        },
        "Action": "SQS:SendMessage",
        "Resource": f"arn:aws:sqs:us-west-2:{account_id}:{queue_name}",
        "Condition": {
            "StringEquals": {
                "aws:SourceAccount": account_id
            },
            "ArnLike": {
                "aws:SourceArn": f"arn:aws:s3:::{bucket_name}"
            }
        }
    }
    policy_json = json.dumps(policy_template)

    try:
        # Attach the policy
        response = sqs_client.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={
                'Policy': policy_json
            }
        )
        print(f"SUCCESS: Policy attached successfully to queue '{queue_name}'.")
    except ClientError as e:
        print(f"FAILURE: ClientError: {e}")
    except Exception as e:
        print(f"FAILURE: An error occurred: {e}")

