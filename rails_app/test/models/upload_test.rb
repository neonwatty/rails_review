require "test_helper"

class UploadTest < ActiveSupport::TestCase
  # test "the truth" do
  #   assert true
  # end

  test "should not save upload without file" do
    upload = Upload.new
    assert_not upload.save
  end
end
