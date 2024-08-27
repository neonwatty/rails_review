from entrypoints.utilities.upload_file_name_validator import validator
import pytest


test_success_data = ["test.mp4", "this is a file.mpg"]


@pytest.mark.parametrize("upload_file_name", test_success_data)
def test_success(upload_file_name):
    check, message = validator(upload_file_name)
    assert check is True, f"FAILURE: upload_file_name failed when it should succeed --> {message}"


test_failure_data = [1, {}, "test.mp3", "test.avi"]


@pytest.mark.parametrize("upload_file_name", test_failure_data)
def test_failure(upload_file_name):
    check, message = validator(upload_file_name)
    assert check is False, f"FAILURE: upload_file_name succeeded when it should fail --> {message}"
