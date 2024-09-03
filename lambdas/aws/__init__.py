import os
import boto3

aws_profile = os.getenv("AWS_PROFILE")
bucket_name = os.getenv("BUCKET_APP")

if aws_profile:
    session = boto3.Session(profile_name=aws_profile, region_name="us-west-2")
else:
    session = boto3.Session(region_name="us-west-2")
