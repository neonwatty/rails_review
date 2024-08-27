from entrypoints.utilities.file_hash_validator import validator
from utilities.tools.hash import hash_file
import pytest

valid_file_hashes = [hash_file("tests/test_files/blank.mp4"), hash_file("tests/test_files/test_file.mp4")]


@pytest.mark.parametrize("file_hash", valid_file_hashes)
def test_success(file_hash):
    check, message = validator(file_hash)
    assert check is True, f"FAILURE: file_hash failed when it should succeed --> {message}"


test_failure_data = [1, {}, "not_a_hash"]


@pytest.mark.parametrize("file_hash", test_failure_data)
def test_failure(file_hash):
    check, message = validator(file_hash)
    assert check is False, f"FAILURE: file_hash succeeded when it should fail --> {message}"
