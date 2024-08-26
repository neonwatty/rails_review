class UploadsController < ApplicationController
  before_action :set_upload, only: %i[show edit update destroy]
  before_action :authenticate_user!, only: %i[new create edit update destroy]

  def index
    @uploads = Upload.all
  end

  def show
  rescue ActiveRecord::RecordNotFound
    redirect_to root_path
  end

  def new
    @upload = Upload.new
  end

  def create
    @upload = Upload.new(upload_params)
    if @upload.save
      redirect_to @upload, notice: 'Upload was successfully created.'
    else
      render :new, status: :unprocessable_entity
    end
  end

  def edit
  end

  def update
    if @upload.update(upload_params)
      redirect_to @upload, notice: 'Upload was successfully updated.'
    else
      render :edit
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
    params.require(:upload).permit(:video)
  end
end
