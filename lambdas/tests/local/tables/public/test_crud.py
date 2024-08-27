import pytest
import os
import uuid
from tables.public.row_create import create
from tables.public.row_read import read
from tables.public.row_update import update
from tables.public.row_destroy import destroy
from supabase import create_client, Client

supabase_client: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

ROOT_USER_ID = os.environ["USER_ID_TEST_1"]

# setup fixtures
test_success_data = [
    (
        "temp-file-ledger",
        "file_id",
        str(uuid.uuid4()),
        {"user_id": ROOT_USER_ID, "file_name": "file_name from a test"},
        {"file_name": "updated file_name test"},
    ),
    (
        "history-ledger",
        "file_id",
        str(uuid.uuid4()),
        {"user_id": ROOT_USER_ID, "exception": "this is an exception"},
        {"exception": "an updated exception"},
    ),
]


@pytest.mark.parametrize("table_name, key, value, document, updated_document", test_success_data)
def test_ledgers(table_name, key, value, document, updated_document, subtests):
    with subtests.test(msg="create"):
        response = create(table_name, key, value, document)
    print(f"table_name --> {table_name}")
    with subtests.test(msg="read"):
        response = read(table_name, key, value)
        assert response is not None
        print(f"response --> {response}")
        assert response[0][key] == value

    with subtests.test(msg="update"):
        response = update(table_name, key, value, updated_document)

    with subtests.test(msg="delete"):
        response = destroy(table_name, key, value)
