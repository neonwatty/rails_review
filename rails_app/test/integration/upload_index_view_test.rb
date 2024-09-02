require "test_helper"

class BlogFlowTest < ActionDispatch::IntegrationTest
  # sign in with first user
  setup 

  setup do
    # Log in the user from the fixture
    @user = users(:one)
    sign_in @user
  end

  test "should access the index page" do
    # Visit the index page (replace 'index_path' with your actual path)
    get "/uploads"
    assert_response :success
    expected_message = "Welcome to #{ENV['APP_NAME_PUBLIC']}"
    assert_select 'h1', expected_message
  end


  # test "can create an upload" do
  #   get "/uploads/new"
  #   assert_response :success

  #   post "/uploads",
  #     params: { upload: { user_id: 1, files_attached: false } }
  #   assert_response :redirect
  #   follow_redirect!
  #   assert_response :success
  #   assert_select "p", "Upload was successfully created."
  # end
end