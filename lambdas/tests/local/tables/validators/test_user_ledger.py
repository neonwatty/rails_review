import pytest
import uuid
from pydantic import ValidationError
from tables.validators.user_ledger import validator


# setup fixtures
success_data = [
    ({"id": str(uuid.uuid4()), "email": "jeremy@gmail.com"}),
]


@pytest.mark.parametrize("input", success_data)
def test_file_success(input):
    assert validator(input) is None


failure_data = [
    ({"user_id": "not an id", "email": "jeremy@gmail.com"}),
    ({"user_id": str(uuid.uuid4()), "email": "jeremy"}),
    ({"user_id": str(uuid.uuid4()), "non_extant_entry": "hi"}),
]


@pytest.mark.parametrize("input", failure_data)
def test_file_failure(input):
    with pytest.raises((ValidationError)) as excinfo:
        validator(input)
