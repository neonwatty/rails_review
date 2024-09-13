require 'test_helper'

class UploadsControllerTest < ActionDispatch::IntegrationTest
  def setup
    @upload = uploads(:one)
  end

  test "should get home" do
    get home_url
    assert_response :success
  end

  test "should get search_page" do
    get search_page_url
    assert_response :success
  end

  test "should get root" do
    get root_url
    assert_response :success
  end


  test "should post search" do
    post search_uploads_url, params: { search: { query: 'example' } }
    assert_response :success
  end
end
