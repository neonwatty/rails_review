require 'test_helper'

class UploadsControllerTest < ActionDispatch::IntegrationTest
  def setup
    @user = users(:one)
    @upload = uploads(:one) 
    sign_in @user 
  end

  test "test_1: index" do
    get uploads_path
    assert_response :success
  end

  test "test_2: new" do
    get new_upload_path
    assert_response :success
  end
  
  test "test_3: show" do
    get upload_path(@upload)
    assert_response :success
  end

  test "test_4: create" do
    post uploads_path
    assert_response :success
  end

  test "test_5: destroy" do
    delete upload_path(@upload)
    assert_response :success
  end

  test "test_6: search" do
    get search_path
    assert_response :success
  end

  test "test_7: search_items success (:source==form provided)" do
    post search_items_uploads_path, params: @valid_query_params, as: :turbo_stream
    assert_response :success
    assert_match /<turbo-stream/, @response.body
  end


end
