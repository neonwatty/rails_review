import os
import boto3
from dotenv import load_dotenv

load_dotenv()

aws_profile = os.getenv("AWS_PROFILE")

if aws_profile:
    session = boto3.Session(profile_name=aws_profile, region_name="us-west-2")
else:
    session = boto3.Session(region_name="us-west-2")
api_gateway_client = session.client("apigateway")
dynamodb_resource = session.resource("dynamodb")
lambda_client = session.client("lambda")

APP_NAME = os.environ["APP_NAME"]
GATEWAY_NUM = os.environ.get("GATEWAY_NUM", 1)
ACCOUNT_ID = os.environ["ACCOUNT_ID"]
STAGE = os.environ.get("STAGE", "dev")
AUTHORIZER_NAME = "gateway-authorizer"
