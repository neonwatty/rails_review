from entrypoints.utilities.action_validator import validator, valid_actions
import pytest


@pytest.mark.parametrize("action", valid_actions)
def test_success(action):
    check, message = validator(action)
    assert check is True, f"FAILURE: action failed when it should succeed --> {message}"


test_failure_data = ["invalid-action", 1, {}]


@pytest.mark.parametrize("action", test_failure_data)
def test_failure(action):
    check, message = validator(action)
    assert check is False, f"FAILURE: action succeeded when it should fail --> {message}"
