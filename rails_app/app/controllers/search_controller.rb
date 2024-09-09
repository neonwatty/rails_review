class SearchController < ApplicationController
  def index
    @query = params[:query]
    @results = Upload.search_by_name(@query)
                 .where(process_complete: true)
                 .limit(10) if @query.present?
    @pagy, @results = pagy(@results)
  end
end