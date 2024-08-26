class Upload < ApplicationRecord
  belongs_to :user
  has_one_attached :video

  before_validation :set_default_user, if: -> { user_id.nil? }

  private

  def set_default_user
    # Find the user with id 1 or the first user in the users table
    self.user = User.first || User.new(id: 1, email: "neonwatty@gmail.com", password: "password", password_confirmation: "password") 
  end
end
