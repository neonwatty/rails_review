require "application_system_test_case"

class NewUploadTest < ApplicationSystemTestCase
  fixtures :all  

  setup do
    @user = users(:one)
  end

  test "test_1: non-logged in user functionality - redirect to sign in" do
    visit new_upload_path
    assert_current_path new_user_session_path
  end

  test "test_1: logged in user functionality - details card" do
    sign_in(@user)
    visit new_upload_path
    assert_current_path new_upload_path
  end

end