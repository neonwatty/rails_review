import pytest
from tables.gateway.row_create import create
from tables.gateway.row_read import read
from tables.gateway.row_delete import delete


test_success_data = [("test_api_id", [])]


@pytest.mark.parametrize("api_id, resource_arns", test_success_data)
def test_file_ledger(api_id, resource_arns, subtests):
    with subtests.test(msg="create"):
        response = create(api_id, resource_arns)
        assert response is None, "FAILURE: secret row create failed"

    with subtests.test(msg="read"):
        response = read(api_id)
        assert "Item" in list(response.keys()), "FAILURE: gateway row reader failed, no Item in response"
        item = response["Item"]
        read_api_id = item["api_id"]
        assert api_id == read_api_id, f"FAILURE: gateway row reader failed, input api_id {api_id} does not match read api_id {read_api_id}"

    with subtests.test(msg="delete"):
        response = delete(api_id)
        assert response is None, "FAILURE: gateway row delete failed"

        response = read(api_id)
        assert "Item" not in list(response.keys()), "FAILURE: gateway row delete failed, Item exists in response"
