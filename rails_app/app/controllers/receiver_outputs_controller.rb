class ReceiverOutputsController < ApplicationController
  protect_from_forgery except: :update
  skip_before_action :verify_authenticity_token, only: :update

  def update
    payload = extract_and_permit_payload

    if payload[:upload_id].nil? || payload[:result].nil?
      render json: { error: 'Invalid payload' }, status: :bad_request and return
    end

    output_record = find_output_record(payload[:upload_id])

    if output_record.nil?
      render json: { error: 'Output record not found' }, status: :not_found and return
    end

    if update_output_record(output_record, payload[:result])
      render json: { message: 'Output updated successfully' }, status: :ok
    else
      render json: { error: 'Failed to update output' }, status: :unprocessable_entity
    end
  end

  private

  def extract_and_permit_payload
    params.require(:output).permit(:upload_id, :result)
  end

  def find_output_record(upload_id)
    Output.find_by(upload_id: upload_id)
  end

  def update_output_record(output_record, result)
    output_record.update(result: result)
  end
end
