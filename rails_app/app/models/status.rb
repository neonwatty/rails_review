class Status < ApplicationRecord
  before_create :set_default_delivery
  before_create :set_default_preprocess
  before_create :set_default_process
  before_create :set_default_end

  belongs_to :upload

  
  private

  def set_default_delivery
    self.receiver_start = "pending"
  end
  def set_default_preprocess
    self.receiver_preprocess = "pending"
  end
  def set_default_process
    self.receiver_process = "pending"
  end
  def set_default_end
    self.receiver_end = "pending"
  end

end
