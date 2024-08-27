import pytest
import uuid
from pydantic import ValidationError
from tables.validators.file_ledger import validator


# setup fixtures
success_data = [
    ({"file_id": str(uuid.uuid4()), "file_name": "farts.txt", "tag_1": "home", "user_id": str(uuid.uuid4())}),
    ({"file_id": str(uuid.uuid4()), "file_name": "farts.txt"}),
]


@pytest.mark.parametrize("input", success_data)
def test_file_success(input):
    assert validator(input) is None


failure_data = [
    ({"file_id": "not an id", "file_name": "farts.txt", "tag_1": "home", "user_id": str(uuid.uuid4())}),
    ({"file_id": str(uuid.uuid4()), "file_name": "f"}),
    ({"file_id": str(uuid.uuid4()), "non_extant_entry": "hi"}),
]


@pytest.mark.parametrize("input", failure_data)
def test_file_failure(input):
    with pytest.raises((ValidationError)) as excinfo:
        validator(input)
