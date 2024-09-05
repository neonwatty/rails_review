import pytest
from aws_scaffold.generators.generate_namespaces import generate_bucket_names
from aws_scaffold.generators.generate_namespaces import generate_queue_names
from aws_scaffold.s3.delete import delete_bucket
from aws_scaffold.sqs.delete import delete_sqs_queue

# generate bucket names
bucket_names = generate_bucket_names()
queue_names = generate_queue_names()


# create buckets
@pytest.mark.parametrize("bucket_name", bucket_names)
def test_create_bucket(bucket_name):
    create_val = delete_bucket(bucket_name)
    assert create_val == True


# create queues
@pytest.mark.parametrize("queue_nane", queue_names)
def test_create_queue(queue_nane):
    create_val = delete_sqs_queue(queue_nane)
    assert create_val == True
