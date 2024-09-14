require "application_system_test_case"

class AllUploadsTest < ApplicationSystemTestCase
  fixtures :all  # Load all fixtures including active_storage ones

  setup do
    @user = users(:one)
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
end
