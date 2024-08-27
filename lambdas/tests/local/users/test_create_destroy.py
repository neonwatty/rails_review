from users.user_create import handler as user_create
from users.user_destroy import handler as user_destroy
from tables.public.row_read import read as public_read
from tables.secrets.row_read import read as secrets_read
import pytest
from faker import Faker

fake = Faker()
random_name = "_".join(fake.name().split(" ")).lower()
success_data = [({"email": f"{random_name}@gmail.com"})]


@pytest.mark.parametrize("data", success_data)
def test_success(data, subtests):
    user_id = None
    with subtests.test(msg="create user"):
        response = user_create(data, {})
        assert response["statusCode"] == 200
        user_id = response["user_id"]

    with subtests.test(msg="check user-ledger"):
        response = public_read("user-ledger", "id", user_id)
        assert "id" in response[0], "FAILURE: user_id not in user-ledger"

    with subtests.test(msg="check secrets-ledger"):
        response = secrets_read(user_id)
        items = response.get("Items") or response.get("Item") or []
        assert len(items) > 0, "FAILURE: user_id not in secrets-ledger"

    with subtests.test(msg="destroy user"):
        response = user_destroy({"user_id": user_id}, {})
        assert response["statusCode"] == 200

    with subtests.test(msg="check user-ledger"):
        response = public_read("user-ledger", "id", user_id)
        assert len(response) == 0

    with subtests.test(msg="check secrets-ledger"):
        response = secrets_read(user_id)
        items = response.get("Items") or response.get("Item") or []
        assert len(items) == 0, "FAILURE: user_id in secrets-ledger"
