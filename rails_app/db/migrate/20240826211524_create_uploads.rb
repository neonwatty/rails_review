class CreateUploads < ActiveRecord::Migration[7.2]
  def change
    create_table :uploads do |t|
      t.belongs_to :user, null: false, foreign_key: true, index: true
      t.string :filename, null: false, limit: 255

      t.timestamps
    end
  end
end
