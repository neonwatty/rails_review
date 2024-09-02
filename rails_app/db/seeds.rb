# This file should ensure the existence of records required to run the application in every environment (production,
# development, test). The code here should be idempotent so that it can be executed at any point in every environment.
# The data can then be loaded with the bin/rails db:seed command (or created alongside the database with db:setup).
#
# Example:
#
#   ["Action", "Comedy", "Drama", "Horror"].each do |genre_name|
#     MovieGenre.find_or_create_by!(name: genre_name)
#   end

# User.find_or_create_by(id: 1) do |user|
#   user.email = "neonwatty@gmail.com"
#   user.password = "password" # Ensure proper password setup
#   user.password_confirmation = "password"
# end

# Upload.find_or_create_by(id: 1, user_id: 1) do |upload|
#   upload.files.attach(io: File.open(Rails.root.join("test/fixtures/files/cover_image.jpeg")), filename: "cover_image.jpeg")
# end
