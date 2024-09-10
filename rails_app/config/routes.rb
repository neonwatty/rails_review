Rails.application.routes.draw do
  devise_for :users, controllers: { confirmations: 'confirmations' }
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check

  # Render dynamic PWA files from app/views/pwa/*
  get "service-worker" => "rails/pwa#service_worker", as: :pwa_service_worker
  get "manifest" => "rails/pwa#manifest", as: :pwa_manifest

  # receiver routes
  post 'receiver_end/update', to: 'receiver_end#update'
  post 'receiver_status/update', to: 'receiver_status#update'
  patch 'receiver_status/update', to: 'receiver_status#update'
  post 'receiver_outputs/update', to: 'receiver_outputs#update'
  patch 'receiver_outputs/update', to: 'receiver_outputs#update'
  

  # search route
  get 'search_page', to: 'uploads#search_page', as: :search_page
  resources :uploads do
    collection do
      post 'search'
    end
  end

  # maker personal routes
  get 'home', to: 'uploads#home', as: :home

  resources :uploads do
    member do
      get 'details_card'
    end
  end

  # catch non-existant pages
  match '*path', to: 'application#not_found', via: :all unless Rails.application.config.assets.compile

  # define root
  root "uploads#index"
end