import pytest
from aws_scaffold import APP_NAME_PRIVATE
from aws_scaffold import receiver_names
from aws_scaffold.generators.generate_namespaces import generate_bucket_names
from aws_scaffold.generators.generate_namespaces import generate_queue_names
from aws_scaffold.s3.delete import delete_bucket
from aws_scaffold.sqs.delete import delete_sqs_queue
from aws_scaffold.ecr.delete import delete_ecr_repository


# delete bucket names
all_bucket_names, bucket_host_pairs = generate_bucket_names()
queue_names = generate_queue_names()


# delete buckets
@pytest.mark.parametrize("bucket_name", all_bucket_names)
def test_delete_bucket(bucket_name):
    create_val = delete_bucket(bucket_name)
    assert create_val == True


# delete queues
@pytest.mark.parametrize("queue_nane", queue_names)
def test_delete_queue(queue_nane):
    create_val = delete_sqs_queue(queue_nane)
    assert create_val == True


# delete ecr repo
@pytest.mark.parametrize("receiver_name", receiver_names)
def test_delete_ecr_repos(receiver_name):
    repo_name = f"{APP_NAME_PRIVATE}-{receiver_name}"
    create_val = delete_ecr_repository(repo_name)
    assert create_val == True
