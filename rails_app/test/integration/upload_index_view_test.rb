require "test_helper"

class BlogFlowTest < ActionDispatch::IntegrationTest
  test "can see the index page" do
    get "/"
    assert_select "h1", "uploads#index"
  end

  test "can create an upload" do
    get "/uploads/new"
    assert_response :success

    post "/uploads",
      params: { upload: { user_id: 1, files_attached: false } }
    assert_response :redirect
    follow_redirect!
    assert_response :success
    assert_select "p", "Upload was successfully created."
  end
end