class Status < ApplicationRecord
  before_create :set_default_delivery
  before_create :set_default_preprocess
  before_create :set_default_process

  belongs_to :upload

  
  private

  def set_default_delivery
    self.delivery = "pending"
  end
  def set_default_preprocess
    self.preprocess = "pending"
  end
  def set_default_process
    self.process = "pending"
  end
end
