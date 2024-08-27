class LambdaFileController < ApplicationController
  skip_before_action :verify_authenticity_token # For API requests
  before_action :authenticate_request

  def processed_image
    processed_image_key = params[:processed_image_key]
    bucket_name = params[:bucket_name]
    upload_id = params[:upload_id]

    upload = Upload.find_by(id: upload_id)

    if upload
      # Download the processed image from S3
      s3 = Aws::S3::Client.new
      processed_image_data = s3.get_object(bucket: bucket_name, key: processed_image_key).body.read
      
      # Attach processed image to the upload's profile
      upload.files.attach(io: StringIO.new(processed_image_data), filename: File.basename(processed_image_key))
      upload.save
      
      render json: { status: 'processed image updated' }
    else
      render json: { error: 'User not found' }, status: :not_found
    end
  end


  private

  def authenticate_request
    # Extract the Authorization header
    auth_header = request.headers['Authorization'] || ''
    # Check if the Authorization header starts with 'Bearer '
    if auth_header.start_with?('Bearer ')
      # Extract the token (API key)
      token = auth_header.split(' ').last
      # Compare the token with your expected API key
      expected_token = Rails.application.config.lambda_api_key
      unless ActiveSupport::SecurityUtils.secure_compare(token, expected_token)
        head :unauthorized
      end
    else
      head :unauthorized
    end
  end
end