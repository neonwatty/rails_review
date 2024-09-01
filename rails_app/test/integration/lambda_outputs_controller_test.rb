require 'test_helper'

class LambdaOutputsControllerTest < ActionDispatch::IntegrationTest

  test 'should update outputs with valid data' do
    # Valid JSON payload
    payload = {
      receiver_outputs: {
        upload_id: 1,
        result: 'this is a result'
      }
    }

    # Send a PATCH request to the receiver_outputs controller
    patch "/receiver_outputs/update", params: payload.to_json, headers: {
      'Content-Type': 'application/json',
      'Authorization': "Bearer #{ENV['LAMBDA_API_KEY_TEST']}"
    }

    # Assert the response status
    assert_response :ok

    # Assert the response message
    assert_equal JSON.parse(response.body)['message'], 'Output updated successfully'

    # Assert the status record is updated
    assert_equal Output.find(1).result, 'this is a result'

  end

end