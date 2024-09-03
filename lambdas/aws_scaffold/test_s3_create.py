import pytest
from aws_scaffold.s3.create import create_bucket
from aws_scaffold.s3.delete import delete_bucket
import random
import time

custom_charset = 'abcdefghijklmnopqrstuvwxyz'

def generate_custom_random_string(length):
    return ''.join(random.choices(custom_charset, k=length))

bucket_names = [f"test-bucket-{generate_custom_random_string(7)}"]

@pytest.mark.parametrize("bucket_name", bucket_names)
def test_create_bucket(bucket_name):
    create_val = create_bucket(bucket_name)
    assert create_val == True


@pytest.mark.parametrize("bucket_name", bucket_names)
def test_destroy_bucket(bucket_name):
    time.sleep(10)
    destroy_val = delete_bucket(bucket_name)
    assert destroy_val == True