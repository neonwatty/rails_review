class AddFilesAttachedToUploads < ActiveRecord::Migration[7.2]
  def change
    add_column :uploads, :files_attached, :boolean
  end
end
