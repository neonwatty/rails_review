require 'test_helper'

class ReceiverEndControllerTest < ActionDispatch::IntegrationTest
  test 'test_1: should update status with valid data' do
    # Valid JSON payload
    payload = {
      receiver_end: { 
        bucket_name: "#{ENV['APP_NAME_PRIVATE']}-integration-test-data",
        processed_image_key: 'integration_test_image.png',
        upload_id: 1
      }
    }

    # Send a POST request to the receiver_status controller
    post "/receiver_end/update", params: payload.to_json, headers: {
      'Content-Type': 'application/json',
      'Authorization': "Bearer #{ENV['LAMBDA_API_KEY_TEST']}"
    }

    # Assert the response status
    assert_response :ok

    # Assert the response message
    assert_equal JSON.parse(response.body)['status'], 'processed image updated'
    
  end

end