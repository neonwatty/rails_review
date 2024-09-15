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

    # Trigger JavaScript to reveal the hidden file input
    page.execute_script("
    var fileInput = document.getElementById('file_input_id');
    if (fileInput) {
      fileInput.style.display = 'block';  // Make the input visible
      fileInput.removeAttribute('disabled');  // Remove the disabled attribute
      }
    ")

    puts page.html

    # Wait for the file input to be visible
    sleep 1

    # click on the file input
    attach_file('upload[files]', Rails.root + 'test/fixtures/files/r_l_burnside.png')

    # submit the form
    click_button 'Submit'

    # STOPPED HERE
    
    # assert redirect to show page
    assert_current_path upload_path(Upload.last)

    # assert flash message
    assert_selector 'div', text: 'Upload was successfully created.'

    # assert that the ActiveStorage blobs count is 2 more than the original count
    assert_equal 2, ActiveStorage::Blob.count - @blob_count

    # assert that the ActiveStorage attachments count is 1 more than the original count
    assert_equal 1, ActiveStorage::Attachment.count - @attachment_count

    # sleep for 30 seconds
    sleep 30

    # assert that the ActiveStorage blobs count is 4 more than the original count
    assert_equal 4, ActiveStorage::Blob.count - @blob_count

    # assert that the ActiveStorage attachments count is 2 more than the original count
    assert_equal 2, ActiveStorage::Attachment.count - @attachment_count

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