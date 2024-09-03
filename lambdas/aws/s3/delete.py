from aws import session
from aws.s3.check import bucket_exists
from botocore.exceptions import ClientError


def delete_bucket(bucket_name: str):
    try:
        # First, delete all objects in the bucket
        bucket = session.resource('s3').Bucket(bucket_name)
        bucket.objects.delete()

        # Now delete the bucket itself
        session.delete_bucket(Bucket=bucket_name)
        print(f"SUCCESS: bucket '{bucket_name}' deleted successfully.")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"FAILURE: bucket '{bucket_name}' does not exist.")
            return False
        elif e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"FAILURE: bucket '{bucket_name}' does not exist or has already been deleted.")
            return False
        elif e.response['Error']['Code'] == 'BucketNotEmpty':
            print(f"FAILURE: bucket '{bucket_name}' is not empty. Ensure all objects are deleted before trying again.")
            return False
        else:
            print(f"FAILURE: ClientError: {e}")
            return False
    except Exception as e:
        print(f"FAILURE: an error occurred: {e}")
        return False
