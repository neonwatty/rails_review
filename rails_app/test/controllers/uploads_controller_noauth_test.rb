require 'test_helper'

class UploadsControllerTest < ActionDispatch::IntegrationTest
  def setup
    @upload = uploads(:one)
  end

  test "test_1: index" do
    get uploads_path
    assert_response :success
  end

  test "test_2: new" do
    get new_upload_path
    assert_redirected_to new_user_session_path
  end
  
  test "test_3: show" do
    get upload_path(@upload)
    assert_redirected_to new_user_session_path
  end

  test "test_4: create" do
    post uploads_path
    assert_redirected_to new_user_session_path
  end

  test "test_5: destroy" do
    delete upload_path(@upload)
    assert_redirected_to new_user_session_path
  end

  test "test_6: search" do
    get search_path
    assert_response :success
  end


end
