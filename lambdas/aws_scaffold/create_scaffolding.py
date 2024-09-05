import pytest
from aws_scaffold import APP_NAME_PRIVATE
from aws_scaffold.generators.generate_namespaces import generate_bucket_names
from aws_scaffold.generators.generate_namespaces import generate_queue_names
from aws_scaffold.generators.generate_namespaces import generate_connection_records
from aws_scaffold.s3.create import create_bucket
from aws_scaffold.sqs.create import create_sqs_queue
from aws_scaffold.generators.generate_connections import create_single_connection
from aws_scaffold.ecr.create import create_ecr_repository
receiver_names = ["receiver_start", "receiver_status", "receiver_preprocess", "receiver_process", "receiver_end"]


# generate bucket names
bucket_names = generate_bucket_names()
queue_names = generate_queue_names()
connection_records = generate_connection_records()


# create buckets
@pytest.mark.parametrize("bucket_name", bucket_names)
def test_create_bucket(bucket_name):
    create_val = create_bucket(bucket_name)
    assert create_val == True


# create queues
@pytest.mark.parametrize("queue_nane", queue_names)
def test_create_queue(queue_nane):
    create_val = create_sqs_queue(queue_nane)
    assert create_val == True


# create connections
@pytest.mark.parametrize("record", connection_records)
def test_create_connection(record):
    create_val = create_single_connection(record)
    assert create_val == True


# create ecr repositories
@pytest.mark.parametrize("receiver_name", receiver_names)
def test_create_ecr_repos(receiver_name):
    repo_name = f"{APP_NAME_PRIVATE}-{receiver_name}"
    create_val = create_ecr_repository(repo_name)
    assert create_val == True