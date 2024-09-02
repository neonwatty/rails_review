require "test_helper"

class BlogFlowTest < ActionDispatch::IntegrationTest
  # sign in with first user
  setup do
    # Log in the user from the fixture
    @user = users(:one)
    @upload = uploads(:one)
    sign_in @user
  end

  test "should access the index page" do
    # Visit the index page (replace 'index_path' with your actual path)
    get "/uploads"
    assert_response :success
    expected_message = "Welcome to #{ENV['APP_NAME_PUBLIC']}"
    assert_select 'h1', expected_message
  end

  test "can create an upload" do
    get "/uploads/new"
    assert_response :success
    assert_select 'form'
  end

  test "should create upload" do
    assert_difference('Upload.count') do
      post uploads_path, params: { upload: { files: fixture_file_upload('cover_image.jpeg') } }
      assert_redirected_to upload_path(Upload.last)
    end
    assert_redirected_to upload_path(Upload.last)
    assert_not_nil flash[:notice]
  end

  test "should destroy upload" do
    assert_difference('Upload.count', -1) do
      delete upload_path(Upload.last)
    end
    assert_redirected_to uploads_path
    assert_not_nil flash[:notice]
  end

end