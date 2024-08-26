# has email and password_digest fields
# has_secure_password password_string and password_confirmation virtual objects
class User < ApplicationRecord
  validates: email, presence: true, uniqueness: true
  has_secure_password
end
