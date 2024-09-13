class UploadsController < ApplicationController
  before_action :set_upload, only: %i[show destroy]
  before_action :authenticate_user!, only: %i[show new create destroy]

  def index
    @uploads = Upload.all
    @pagy, @uploads = pagy(@uploads)
  end

  def new
    @upload = Upload.new
  end

  def show
    @upload = Upload.find(params[:id])
  rescue ActiveRecord::RecordNotFound
    redirect_to root_path
  end 

  def create
    @upload = Upload.new(upload_params)
    if @upload.save
      redirect_to upload_path(@upload), notice: 'Upload was successfully created.'
    else
      render :new
    end
  end

  def destroy
    @upload.destroy
    redirect_to uploads_url, notice: 'Upload was successfully destroyed.'
  end

  def search
  end

  def search_uploads
    @query=params[:query]
    @uploads = Upload.search_by_name(@query)
    .where(process_complete: true)
    .limit(10) || []
    respond_to do |format|
      format.turbo_stream do
          if @query.blank?
            render turbo_stream: turbo_stream.update("search_results", partial: "uploads/no_search")
          else
            render turbo_stream: turbo_stream.update("search_results", partial: "uploads/search_results", locals: { uploads: @uploads })
          end
        end
    end
  end

  private

  def set_upload
    @upload = Upload.find(params[:id])
  end

  def upload_params
    params.require(:upload).permit(:files)
  end
end
