require "test_helper"

class UploadTest < ActiveSupport::TestCase
  # test "the truth" do
  #   assert true
  # end

  test "should not save upload without file" do
    upload = Upload.create(id: 2, user_id: 1)
    assert_not upload.save
  end
end
