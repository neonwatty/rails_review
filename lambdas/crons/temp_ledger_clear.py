import os
from tables.public.row_destroy import destroy
from s3.subdir_delete import delete_subdir
from datetime import datetime, timezone
from tables.public import supabase_client

FILE_LEDGER_TEMP = os.environ["FILE_LEDGER_TEMP"]


def check_temp_file_ledger() -> list:
    try:
        # query temp file ledger for failed == true rows
        response = supabase_client.table(FILE_LEDGER_TEMP).select("file_id, file_metadata.s3_data").eq("failed", "true").execute()
        data_failed = response.data

        # Define the timestamp you're comparing against
        current_time = datetime.now(tz=timezone.utc).isoformat()

        # Query the table and filter by timestamp
        response = supabase_client.table(FILE_LEDGER_TEMP).select("file_id, file_metadata.s3_data").lt("last_updated", current_time).execute()
        data_timeout = response.data

        # merge dead_file_ids
        dead_file_ids = []
        if len(data_failed) > 0:
            dead_file_ids += [v for v in data_failed]
        if len(data_timeout) > 0:
            dead_file_ids += [v for v in data_timeout]
        dead_file_ids = list(set(dead_file_ids))

        return dead_file_ids
    except Exception as e:
        failure_message = f"FAILURE: check_temp_file_ledger failed with exception {e}"
        print(failure_message)
        raise e


def main():
    # use check_temp_file_ledger to return failed / old entries from temp file ledger
    dead_entries = check_temp_file_ledger()

    # loop over each entry, find the bucket_name and subdir associated with each, and delete subdir
    for dead_entry in dead_entries:
        # extract s3 data subdir info
        s3_data = dead_entry["file_metadata"]["s3_data"]
        bucket_name = s3_data["bucket_name"]
        subdir = s3_data["subdir"]

        # delete subdir
        delete_subdir(subdir, bucket_name)

        # delete row in file_ledger based on file_id
        file_id = dead_entry["file_id"]
        destroy(FILE_LEDGER_TEMP, "file_id", file_id)
