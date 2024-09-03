from aws_scaffold import session, ACCOUNT_ID

s3_client = session.client("s3", region_name='us-west-2')

def configure_s3_bucket_notification(bucket_name: str, queue_name: str, suffix=None) -> bool:
    # convert queue_name to arn
    queue_arn = f"arn:aws:sqs:us-west-2:{ACCOUNT_ID}:{queue_name}"

    # Define the notification configuration
    queue_configuration = {
        'QueueArn': queue_arn,
        'Events': [
            's3:ObjectCreated:*'
        ]
    }

    if suffix:
        queue_configuration['Filter'] = {
            'Key': {
                'FilterRules': [
                    {
                        'Name': 'suffix',
                        'Value': suffix
                    }
                ]
            }
        }

    notification_configuration = {
        'QueueConfigurations': [queue_configuration]
    }

    try:
        # Set the notification configuration
        s3_client.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration=notification_configuration
        )
        print(f"SUCCESS: Notification configuration set for bucket '{bucket_name}' with suffix '{suffix}'.")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
