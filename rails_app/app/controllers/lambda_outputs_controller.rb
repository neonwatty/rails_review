class LambdaOutputsController < ApplicationController
  protect_from_forgery except: :update
  skip_before_action :verify_authenticity_token, only: :update

  def update
    # Parse and permit the JSON payload
    payload = params.require(:output).permit(:upload_id, :result)

    upload_id = payload[:upload_id]
    result = payload[:result]

    # Find the output record by upload_id
    output_record = Output.find_by(upload_id: upload_id)

    if output_record.nil?
      render json: { error: 'Output record not found' }, status: :not_found and return
    end

    # Update the result column
    output_record.update(result: result)

    if output_record.save
      render json: { message: 'Output updated successfully' }, status: :ok
    else
      render json: { error: 'Failed to update output' }, status: :unprocessable_entity
    end
  end
end
