import pytest
from tables.secrets.row_create import create
from tables.secrets.row_read import read
from tables.secrets.row_update import update
from tables.secrets.row_delete import delete
from tables.secrets.row_read import read_gsi
from tables.secrets.row_read import read_api_key


test_success_data = [("test_user_id", "test_api_id")]

new_api_id = "test_new_api_id"


@pytest.mark.parametrize("user_id, api_id", test_success_data)
def test_crud(user_id, api_id, subtests):
    api_key_read = None
    user_id_read = None
    with subtests.test(msg="create"):
        response = create(user_id, api_id)
        assert response is None, "FAILURE: secret row create failed"

    with subtests.test(msg="read user_id"):
        response = read(user_id)
        assert "Item" in list(response.keys()), "FAILURE: secrets row reader failed, no Item in response"
        item = response["Item"]
        user_id_read = item["user_id"]
        assert user_id == user_id_read, f"FAILURE: secrets row reader failed, input user_id {user_id} does not match read user_id {read_user_id}"
        api_key_read = item["api_key"]

    with subtests.test(msg="read api_key"):
        response = read_api_key(api_key_read)
        user_id = item["user_id"]
        assert user_id == user_id_read, f"FAILURE: secrets row reader failed, input user_id {user_id} does not match read user_id {read_user_id}"

    with subtests.test(msg="update api_id"):
        response = update(user_id, api_id=new_api_id)
        assert response is None, "FAILURE: secrets row update failed"
        response = read(user_id)
        assert "Item" in list(response.keys()), "FAILURE: secrets row reader failed, no Item in response"
        item = response["Item"]
        read_user_id = item["user_id"]
        assert user_id == read_user_id, f"FAILURE: secrets row reader failed, input user_id {user_id} does not match read user_id {read_user_id}"
        read_api_id = item["api_id"]
        assert new_api_id == read_api_id, f"FAILURE: secrets row reader failed, new_api_id {new_api_id} does not match read_api_id {read_api_id}"

    with subtests.test(msg="update api_key"):
        response = read(user_id)
        assert "Item" in list(response.keys()), "FAILURE: secrets row reader failed, no Item in response"
        item = response["Item"]
        old_api_key = item["api_key"]
        assert user_id == read_user_id, f"FAILURE: secrets row reader failed, input user_id {user_id} does not match read user_id {read_user_id}"

        response = update(user_id, api_key=True)
        assert response is None, "FAILURE: secrets row update failed"
        response = read(user_id)
        assert "Item" in list(response.keys()), "FAILURE: secrets row reader failed, no Item in response"
        item = response["Item"]
        read_api_id = item["user_id"]
        assert user_id == read_user_id, f"FAILURE: secrets row reader failed, input user_id {user_id} does not match read user_id {read_user_id}"
        new_api_key = item["api_key"]
        assert old_api_key != new_api_key, f"FAILURE: secrets row reader failed, new_api_key and old_api_key the same"

    with subtests.test(msg="delete"):
        response = delete(user_id)
        assert response is None, "FAILURE: secrets row delete failed"

        response = read(user_id)
        assert "Item" not in list(response.keys()), "FAILURE: secrets row delete failed, Item exists in response"


def test_gsi_read(subtests):
    gsi_entries = [("USER_ID_TEST_1", "test_api_id_1"), ("USER_ID_TEST_2", "test_api_id_1"), ("test_user_id_3", "test_api_id_2")]

    for num, entry in enumerate(gsi_entries):
        with subtests.test(msg=f"create {num+1} entry"):
            response = create(entry[0], entry[1])
            assert response is None, "FAILURE: secret row create failed"

    with subtests.test(msg="gsi read"):
        response = read_gsi(gsi_entries[0][1])
        items = response.get("Items", [])
        assert len(items) == 2, "FAILURE: gsi_read test failed"

    for num, entry in enumerate(gsi_entries):
        with subtests.test(msg=f"delete {num+1} entry"):
            response = delete(entry[0])
            assert response is None, "FAILURE: secret row delete failed"
