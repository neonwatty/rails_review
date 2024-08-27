from unittest.mock import MagicMock, patch
from decorators.warmer import warmer


# Sample function to be decorated
def sample_handler(event, context):
    return {"statusCode": 200, "body": "Handler Response"}


# Apply the warmer decorator to the sample function
decorated_handler = warmer(sample_handler)


def test_warmer_decorator_warmup():
    # Arrange
    event = {"source": "warmer-test-dev-handler"}
    context = {}

    # Patch print to capture its output
    with patch("builtins.print") as mock_print:
        # Act
        result = decorated_handler(event, context)

        # Assert
        mock_print.assert_called_once_with("WarmUp - Lambda is warm!")
        assert result == {}


def test_warmer_decorator_no_warmup():
    # Arrange
    event = {"source": "some-other-source"}
    context = {}

    # Act
    result = decorated_handler(event, context)

    # Assert
    assert result == {"statusCode": 200, "body": "Handler Response"}
