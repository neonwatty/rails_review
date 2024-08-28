# app/services/lambda_invoker.rb
require 'aws-sdk-lambda'

class LambdaInvoker
  def initialize
    @client = Aws::Lambda::Client.new(region: ENV['AWS_REGION'])
  end

  def invoke_function(file_key, upload_id, user_id)
    payload = {
      message: 'File uploaded successfully',
      upload_id: upload_id,
      user_id: user_id,
      file_key: file_key,
      bucket_name: ENV["AWS_RAILS_INBOUND_BUCKET"],
      stage: Rails.env 
    }.to_json

    response = @client.invoke({
      function_name: ENV['RECEIVER_START_LAMBDA'],
      invocation_type: 'Event',
      payload: payload
    })
    Rails.logger.info("Lambda function invoked: #{response}")
  rescue StandardError => e
    Rails.logger.error("Error invoking Lambda function: #{e.message}")
  end
end
