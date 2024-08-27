class LambdaController < ApplicationController
  skip_before_action :verify_authenticity_token # For API requests

  def processed_image
    processed_image_key = params[:processed_image_key]
    bucket_name = params[:s3_bucket_name]
    upload_id = params[:upload_id]

    upload = Upload.find_by(id: upload_id)

    if upload
      # Download the processed image from S3
      s3 = Aws::S3::Client.new
      processed_image_data = s3.get_object(bucket: bucket_name, key: processed_image_key).body.read
      
      # Attach processed image to the upload's profile
      upload.profile_image.attach(io: StringIO.new(processed_image_data), filename: File.basename(processed_image_key))
      upload.save
      
      render json: { status: 'processed image updated' }
    else
      render json: { error: 'User not found' }, status: :not_found
    end
  end
end