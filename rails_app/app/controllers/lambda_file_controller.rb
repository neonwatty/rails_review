class LambdaFileController < ApplicationController
  skip_before_action :verify_authenticity_token # For API requests
  before_action :authenticate_request

  def processed_image
    upload = Upload.find_by(id: params[:upload_id])

    if upload
      process_and_attach_image(
        processed_image_key: params[:processed_image_key],
        bucket_name: params[:bucket_name],
        upload: upload
      )
      render json: { status: 'processed image updated' }
    else
      render json: { error: 'User not found' }, status: :not_found
    end
  end

  private

  def authenticate_request
    auth_header = request.headers['Authorization'] || ''
    if auth_header.start_with?('Bearer ')
      token = auth_header.split(' ').last
      expected_token = Rails.application.config.lambda_api_key
      head :unauthorized unless ActiveSupport::SecurityUtils.secure_compare(token, expected_token)
    else
      head :unauthorized
    end
  end

  def process_and_attach_image(processed_image_key:, bucket_name:, upload:)
    s3 = Aws::S3::Client.new
    processed_image_data = s3.get_object(bucket: bucket_name, key: processed_image_key).body.read
    
    upload.files.attach(io: StringIO.new(processed_image_data), filename: File.basename(processed_image_key))
    upload.save

    s3.delete_object(bucket: bucket_name, key: processed_image_key)
rescue Aws::S3::Errors::ServiceError => e
    Rails.logger.error "S3 Error: #{e.message}"
end