require "test_helper"

class UploadTest < ActiveSupport::TestCase
  test "should save upload" do
    upload = Upload.create(id: 1, user_id: 1, file: "file")
    assert upload.save
  end

  test "should not save upload without user_id" do
    upload = Upload.create(id: 1, file: "file")
    assert_not upload.save
  end
end
