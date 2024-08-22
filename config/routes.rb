Rails.application.routes.draw do
  devise_for :users
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  resources :blog_posts # Defines the routes for the BlogPostsController


  # get "/new", to: "blog_posts#new", as: :new_blog_post
  # post "/new ", to: "blog_posts#create", as: :blog_posts
  # get "/:id", to: "blog_posts#show", as: :blog_post
  # patch "/:id", to: "blog_posts#update"
  # delete "/:id", to: "blog_posts#destroy"
  # get "/:id/edit", to: "blog_posts#edit", as: :edit_blog_post
 


  # Defines the root path route ("/")
  root "blog_posts#index"
end
