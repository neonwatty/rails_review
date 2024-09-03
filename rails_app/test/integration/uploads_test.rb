require "test_helper"

class BlogFlowTest < ActionDispatch::IntegrationTest
  # turn off transaction wrapper
  self.use_transactional_tests = false

  # sign in with first user
  setup do
    # Log in the user from the fixture
    @user = users(:one)
    sign_in @user
  end

  test "test 1: should access the index page" do
    # Visit the index page (replace 'index_path' with your actual path)
    get "/uploads"
    assert_response :success
    expected_message = "Welcome to #{ENV['APP_NAME_PUBLIC']}"
    assert_select 'h1', expected_message
  end

  test "test 2: can create an upload" do
    get "/uploads/new"
    assert_response :success
    assert_select 'form'
  end

  test "test 3: should create upload" do
    # upload file
    assert_difference('Upload.count') do
      post uploads_path, params: { upload: { files: fixture_file_upload('cover_image.jpeg') } }
      assert_redirected_to upload_path(Upload.last)
    end
    
    # ensure redirect
    assert_redirected_to upload_path(Upload.last)
    assert_not_nil flash[:notice]

    # Define maximum attempts and wait time between checks
    max_attempts = 15
    wait_time = 3 # seconds
    final_status = nil

    max_attempts.times do |attempt|
      sleep(wait_time) # Wait for the specified duration

      status_record = Status.find_by(upload_id: Upload.last)
      final_status = { start: status_record.receiver_start, preprocess: status_record.receiver_preprocess, process: status_record.receiver_process }

      # Break the loop if status is complete
      if final_status[:start] == 'complete' && final_status[:preprocess] == 'complete' && final_status[:process] == 'complete'
        break
      end
    end

    # Assert that the final status is complete after all attempts
    assert_equal 'complete', final_status[:start], "Expected 'complete' for receiver_start but got #{final_status[:start]}"
    assert_equal 'complete', final_status[:preprocess], "Expected 'complete' for receiver_preprocess but got #{final_status[:preprocess]}"
    assert_equal 'complete', final_status[:process], "Expected 'complete' for receiver_process but got #{final_status[:process]}"

    # Assert that the ActiveStorage blobs count is 2
    max_attempts = 10
    wait_time = 3 # seconds
    blob_count = nil

    max_attempts.times do |attempt|
      sleep(wait_time) # Wait for the specified duration

      blob_count =  ActiveStorage::Blob.count

      # Break the loop if status is complete
      if blob_count == 2
        break
      end
    end

    assert_equal 2, ActiveStorage::Blob.count, "Expected 2 blobs but found #{ActiveStorage::Blob.count}"
  end

end