import os
import boto3

AWS_PROFILE = os.getenv("AWS_PROFILE")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

print(f"AWS_PROFILE --> {AWS_PROFILE}")

if AWS_PROFILE:
    session = boto3.Session(profile_name=AWS_PROFILE, region_name="us-west-2")
else:
    session = boto3.Session(region_name="us-west-2")
