import time
from sqs.messages import sqs_client


def message_poll(queue_name: str, target_message_id: str) -> dict | None:
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        # Poll the queue
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,  # Adjust based on your needs
            WaitTimeSeconds=5,  # Long polling
        )

        if "Messages" in response:
            for message in response["Messages"]:
                if message.get("MessageId") == target_message_id:
                    sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
                    return message["ReceiptHandle"]

        # Increment attempt counter and wait before next poll
        attempt += 1
        time.sleep(5)
