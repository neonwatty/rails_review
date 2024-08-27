class CreateStatuses < ActiveRecord::Migration[7.2]
  def change
    create_table :statuses do |t|
      t.belongs_to :upload, null: false, foreign_key: true
      t.string :delivery
      t.string :preprocess
      t.string :process

      t.timestamps
    end
  end
end
