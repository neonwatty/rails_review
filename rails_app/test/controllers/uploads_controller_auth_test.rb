require 'test_helper'

class UploadsControllerTest < ActionDispatch::IntegrationTest
  def setup
    @user = users(:one)
    @upload = uploads(:one) 
    sign_in @user 
  end

  # success - show new create edit update destroy
  test "test_1: should get upload_path with sign in - success response from upload_path" do
    # Make the request to the upload_path
    get upload_path(@upload)

    # Assert that the response is successful (HTTP status code 200)
    assert_response :success
  end

end
