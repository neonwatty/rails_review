class ReceiverStatusController < ApplicationController
  # Ensuring this action can handle JSON requests
  protect_from_forgery except: :update
  skip_before_action :verify_authenticity_token, only: :update

  def update
    # Parse the JSON payload
    payload = params.require(:receiver_status).permit(:lambda, :user_id, :upload_id, :status)
    
    # Extract values from the payload
    lambda_function = payload[:lambda]
    user_id = payload[:user_id]
    upload_id = payload[:upload_id]
    status = payload[:status]

    # Validate the status value
    unless ['complete', 'in_progress', 'failed'].include?(status)
      render json: { error: 'Invalid status' }, status: :unprocessable_entity and return
    end

   # Read lambda names from environment variables
   lambda_names = ENV['RECEIVER_NAMES'].to_s.split(',')

    # Find the status record by upload_id
    status_record = Status.find_by(upload_id: upload_id)

    if status_record.nil?
      render json: { error: 'Status record not found' }, status: :not_found and return
    end

    # Ensure lambda_function is one of the accepted values
    if lambda_names.include?(lambda_function)
      # Update the status record with the lambda's return value
      status_record.update(lambda_function => status)

      if status_record.save
        render json: { message: 'Status updated successfully' }, status: :ok
      else
        render json: { error: 'Failed to update status' }, status: :unprocessable_entity
      end
    else
      render json: { error: 'Invalid lambda function' }, status: :unprocessable_entity
    end
  end
end
