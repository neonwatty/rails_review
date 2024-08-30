class Upload < ApplicationRecord
  belongs_to :user
  has_many_attached :files
  has_one :status, dependent: :destroy
  has_one :output, dependent: :destroy
  after_create :create_status
  after_create :create_output

  validates :files, presence: true
  before_validation :set_default_user, if: -> { user_id.nil? }
  after_commit :check_and_invoke_lambda, on: :create

  private
  def check_and_invoke_lambda
    if files.attached? && !files_attached
      # Check if this is the first file being attached
      if files.count == 1
        file_key = files.first.key # Get the key of the first attached file
        # Pass upload_id and user_id to the LambdaInvoker
        LambdaStarter.new.invoke_function(file_key, id, user_id)
        update(files_attached: true)
      end
    end
  end

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