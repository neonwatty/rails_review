import pytest
from aws_scaffold.s3.create import create_bucket
from aws_scaffold.s3.delete import delete_bucket
from aws_scaffold.sqs.create import create_sqs_queue
from aws_scaffold.sqs.delete import delete_sqs_queue
from aws_scaffold.sqs.attach_policy import attach_policy_to_sqs_queue
import random
import time

custom_charset = 'abcdefghijklmnopqrstuvwxyz'
def generate_custom_random_string(length):
    return ''.join(random.choices(custom_charset, k=length))
  
# create test bucket_name and queue_name
bucket_name = f"test-bucket-{generate_custom_random_string(7)}"
def test_create_bucket():
    val = create_bucket(bucket_name)
    assert val == True
    
queue_name = f"test-queue-{generate_custom_random_string(7)}"
def test_create_queue():
    val = create_sqs_queue(queue_name)
    assert val == True

# create connection between them
def test_attach_policy_to_sqs():
    val = attach_policy_to_sqs_queue(queue_name, bucket_name)
    if val is not True:
        destroy_val = delete_bucket(bucket_name)
        assert destroy_val == True
        
        destroy_val = delete_sqs_queue(queue_name)
        assert destroy_val == True
    assert val == True

# destroy bucket and queue
def destroy_bucket_and_queue():
    destroy_val = delete_bucket(bucket_name)
    assert destroy_val == True
    
    destroy_val = delete_sqs_queue(queue_name)
    assert destroy_val == True