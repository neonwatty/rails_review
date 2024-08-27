import pytest
from s3.object_upload import upload
from s3.object_exist import exist
from s3.object_delete import delete
from s3.subdir_delete import list_subdir
from s3.subdir_delete import delete_subdir
import os

bucket_name = os.environ["BUCKET_TEST"]

success_data = [
    ("dev", "0", "0", "tests/test_files/blank_1.txt"),
]


@pytest.mark.parametrize("stage, user_id, file_id, filepath", success_data)
def test_file_success(stage, user_id, file_id, filepath, subtests):
    filename = filepath.split("/")[-1]
    with subtests.test(msg="create"):
        response = upload(user_id, file_id, filepath, bucket_name, stage)
        assert response.status_code >= 200 and response.status_code < 300, f"FAILURE: s3 create failed with status code {response.status_code}"

    with subtests.test(msg="exist"):
        response = exist(bucket_name, f"{stage}/{user_id}/{file_id}/{filename}")
        assert response is True, "FAILURE: s3 exist failed"

    with subtests.test(msg="delete"):
        response = delete(bucket_name, f"{stage}/{user_id}/{file_id}/{filename}")
        assert response is True, "FAILURE: s3 delete failed"


def test_create_delete_subdir(subtests):
    # upload signatures
    uploads = [
        ("dev", "0", "0", "tests/test_files/blank_1.txt"),
        ("dev", "0", "0", "tests/test_files/blank_2.txt"),
        ("dev", "0", "0", "tests/test_files/blank_3.txt"),
    ]

    # upload items
    for num, item in enumerate(uploads):
        stage, user_id, file_id, filepath = item
        with subtests.test(msg=f"upload item num {num + 1}"):
            response = upload(user_id, file_id, filepath, bucket_name, stage)
            assert response.status_code >= 200 and response.status_code < 300, f"FAILURE: s3 create failed with status code {response.status_code}"

    # check subdirectory count
    subdir = "dev/0/0"
    subdir_contents = list_subdir(bucket_name, subdir)
    assert len(subdir_contents) == 3

    # delete subdirectory
    delete_subdir(bucket_name, subdir)

    # check subdirectory count again
    subdir_contents = list_subdir(bucket_name, subdir)
    assert len(subdir_contents) == 0
