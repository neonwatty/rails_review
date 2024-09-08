class SearchController < ApplicationController
  def index
    @query = params[:query]
    @results = Upload.search_by_name(@query).limit(10) if @query.present?
  end
end