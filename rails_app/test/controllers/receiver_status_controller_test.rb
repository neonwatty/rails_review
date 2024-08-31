# test/controllers/receiver_status_controller_test.rb
require 'test_helper'

class ReceiverStatusControllerTest < ActionDispatch::IntegrationTest
  setup do
    @status = Status.create!(upload_id: 'upload123', some_other_attribute: 'value') # Adjust as needed
    ENV['RECEIVER_NAMES'] = 'receiver_start,receiver_preprocess,receiver_process,receiver_end' # Set this to match expected lambda names
  end

  test "should update status with valid parameters" do
    patch receiver_status_url, 
          params: { receiver_status: { lambda: 'receiver_start', user_id: 1, upload_id: @status.upload_id, status: 'complete' } },
          as: :json
          
    assert_response :ok
    assert_equal 'Status updated successfully', JSON.parse(response.body)['message']
    assert_equal 'complete', @status.reload.lambda1 # Check if status is updated correctly
  end

  test "should not update status with invalid status" do
    patch receiver_status_url, 
          params: { receiver_status: { lambda: 'receiver_start', user_id: 1, upload_id: @status.upload_id, status: 'unknown' } },
          as: :json
          
    assert_response :unprocessable_entity
    assert_equal 'Invalid status', JSON.parse(response.body)['error']
  end

  test "should not update status with missing record" do
    patch receiver_status_url, 
          params: { receiver_status: { lambda: 'receiver_start', user_id: 1, upload_id: 'nonexistent', status: 'complete' } },
          as: :json
          
    assert_response :not_found
    assert_equal 'Status record not found', JSON.parse(response.body)['error']
  end

  test "should not update status with invalid lambda function" do
    patch receiver_status_url, 
          params: { receiver_status: { lambda: 'invalid_lambda', user_id: 1, upload_id: @status.upload_id, status: 'complete' } },
          as: :json
          
    assert_response :unprocessable_entity
    assert_equal 'Invalid lambda function', JSON.parse(response.body)['error']
  end

  test "should not update status with failed update" do
    # Simulate a situation where the status record fails to save
    Status.any_instance.stubs(:save).returns(false)

    patch receiver_status_url, 
          params: { receiver_status: { lambda: 'receiver_start', user_id: 1, upload_id: @status.upload_id, status: 'complete' } },
          as: :json
          
    assert_response :unprocessable_entity
    assert_equal 'Failed to update status', JSON.parse(response.body)['error']
  end

  private

  def receiver_status_url
    '/receiver_status/update'
  end
end
