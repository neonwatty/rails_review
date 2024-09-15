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

  test "test_2: logged in user functionality - details card" do
    sign_in(@user)
    visit new_upload_path
    assert_current_path new_upload_path
  end

  test "test_3: logged in user functionality - details card and new upload" do
    sign_in(@user)
    visit new_upload_path
    assert_current_path new_upload_path
    original_blob_count = ActiveStorage::Blob.count
    original_attachment_count = ActiveStorage::Attachment.count

    # Trigger JavaScript to reveal the hidden file input
    page.execute_script("
    var fileInput = document.getElementById('file_input_id');
    if (fileInput) {
      fileInput.style.display = 'block';  // Make the input visible
      fileInput.removeAttribute('disabled');  // Remove the disabled attribute
      }
    ")

    # Wait for the file input to be visible
    sleep 1
    
    # click on the file input
    attach_file('upload[files]', Rails.root + 'test/fixtures/files/r_l_burnside.png')

    # submit the form
    click_button 'Submit'

    # sleep for 5 seconds
    sleep 5

    # assert redirect to show page
    assert_current_path upload_path(Upload.last)

    sleep 15

    # assert that the ActiveStorage blobs count is 2 more than the original count
    assert_equal 2, ActiveStorage::Blob.count - original_blob_count

    # assert that the ActiveStorage attachments count is 1 more than the original count
    assert_equal 2, ActiveStorage::Attachment.count - original_attachment_count

    # print details of all uploads, status, and blobs
    puts "Upload.all: #{Upload.all.inspect}"
    puts "Status.all: #{Status.all.inspect}"
    puts "ActiveStorage::Blob.all: #{ActiveStorage::Blob.all.inspect}"

    ### STOPPED HERE  - LOOK AT SCREENSHOT, IMAGE NOT SHOWING UP ###
    ### WE SHOULD ASSERT THAT BOTH BEFORE / AFTER IMAGES ARE SHOWING UP ### 

    # assert that upload process_complete is true
    assert_equal true, Upload.last.process_complete

    # assert that upload status_complete is true
    assert_equal true, Upload.last.status_complete

    # destroy the upload
    click_link 'Delete' 

    # click ok on the confirm dialog
    page.driver.browser.switch_to.alert.accept

    # assert redirect to index page
    assert_current_path uploads_path

    # assert flash message
    assert_selector 'div', text: 'Upload was successfully destroyed.'

    # assert that the ActiveStorage blobs count is the same as the original count
    assert_equal @blob_count, ActiveStorage::Blob.count

    # assert that the ActiveStorage attachments count is the same as the original count
    assert_equal @attachment_count, ActiveStorage::Attachment.count
  end

end