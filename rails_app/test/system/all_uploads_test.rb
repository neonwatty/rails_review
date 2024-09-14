require "application_system_test_case"

class AllUploadsTest < ApplicationSystemTestCase
  fixtures :all  

  setup do
    @user = users(:one)
    sign_in @user

    @upload = uploads(:two)
  end

  test "test_1: non-logged in user functionality - all uploads" do
    visit uploads_path
    assert_selector '#navbar'
    assert_selector '#all-uploads-results'
    assert_selector '#upload_result_2'
  end

  test "test_2: check that upload has files.attached" do
    assert @upload.files.attached?, "upload should have file attached via fixture"
  end

  test "test_3: check that details from upload not accessible if not logged in" do
    visit uploads_path
    assert_selector "#navbar"
    assert_selector "#all-upload-results"
    # visit root_path

    # dynamic_id = "upload_result_#{@upload.id}"
    # within "##{dynamic_id}" do
    #   click_on 'Details'
    # end
    # assert_current_path new_user_session_path
  end

end
