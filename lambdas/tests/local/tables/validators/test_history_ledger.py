import pytest
import uuid
from pydantic import ValidationError
from tables.validators.history_ledger import validator


success_data = [
    ({"request_id": str(uuid.uuid4()), "user_id": str(uuid.uuid4()), "exception": "home"}),
    (
        {
            "request_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
        }
    ),
]


@pytest.mark.parametrize("input", success_data)
def test_file_success(input):
    assert validator(input) is None


failure_data = [
    ({"request_id": "not an id"}),
    ({"request_id": str(uuid.uuid4()), "user_id": "not an id"}),
    ({"request_id": str(uuid.uuid4()), "non_extant_entry": "hi"}),
]


@pytest.mark.parametrize("input", failure_data)
def test_file_failure(input):
    with pytest.raises((ValidationError)) as excinfo:
        validator(input)
