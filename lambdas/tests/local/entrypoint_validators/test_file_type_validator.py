from entrypoints.utilities.file_type_validator import validator, valid_file_types
import pytest


@pytest.mark.parametrize("file_type", valid_file_types)
def test_success(file_type):
    check, message = validator(file_type)
    assert check is True, f"FAILURE: file_type failed when it should succeed --> {message}"


test_failure_data = [1, {}]


@pytest.mark.parametrize("file_type", test_failure_data)
def test_failure(file_type):
    check, message = validator(file_type)
    assert check is False, f"FAILURE: file_type succeeded when it should fail --> {message}"
