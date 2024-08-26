class Upload < ApplicationRecord
  belongs_to :user
  has_one_attached :video
  has_one :status, dependent: :destroy
  has_one :output, dependent: :destroy
  after_create :create_status
  after_create :create_output


  before_validation :set_default_user, if: -> { user_id.nil? }

  private

  def set_default_user
    self.user = User.find(1)
  end
  def create_status
    Status.create(upload: self)
  end
  def create_output
    Output.create(upload: self)
  end
end