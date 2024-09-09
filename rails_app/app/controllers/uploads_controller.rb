class UploadsController < ApplicationController
  before_action :set_upload, only: %i[show edit update destroy]
  before_action :authenticate_user!, only: %i[show new create edit update destroy]

  def index
    @uploads = Upload.all
    @pagy, @uploads = pagy(@uploads)
  end

  def search
    @query = params[:query]
    Rails.logger.info "Query: #{@query}"
  
    if @query.present?
      @results = Upload.search_by_name(@query)
                       .where(process_complete: true)
                       .limit(10)
      Rails.logger.info "Results after search: #{@results.inspect}"
    else
      @results = []
    end
  
    @results = [] if @results.nil?
    Rails.logger.info "Results after nil check: #{@results.inspect}"
  
    @pagy, @results  = @results.present? ? pagy(@results) : []
    Rails.logger.info "Pagy results: #{@results.inspect}"
  end

  def show
  rescue ActiveRecord::RecordNotFound
    redirect_to root_path
  end

  def new
    @upload = Upload.new
  end

  def details_card
    @upload = Upload.find(params[:id])
  end 

  def create
    @upload = Upload.new(upload_params)
    if @upload.save
      redirect_to details_card_upload_path(@upload), notice: 'Upload was successfully created.'
    else
      render :new
    end
  end

  def edit
  end

  def update
    @upload = Upload.find(params[:user_id])
    @upload.files.attach(params[:processed_image_key])
    if @upload.save
      redirect_to @upload, notice: 'Update was successfully created.'
    else
      render json: { errors: @user.errors.full_messages }, status: :unprocessable_entity
    end
  end

  def destroy
    @upload.destroy
    redirect_to uploads_url, notice: 'Upload was successfully destroyed.'
  end

  private

  def set_upload
    @upload = Upload.find(params[:id])
  end

  def upload_params
    params.require(:upload).permit(:files)
  end
end
