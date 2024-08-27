import re
from pathlib import Path

MAX_UPLOAD_FILE_NAME_LENGTH = 128

allowed_extensions = (".mp4", ".mpg")

# define pattern for valid file names
upload_file_names_pattern = r"^[a-zA-Z0-9 _,.-]+(\.[a-zA-Z0-9]+)?$"


def is_valid_upload_file_name(upload_file_name: str) -> bool:
    return bool(re.match(upload_file_names_pattern, upload_file_name))


def has_video_extension(filepath):
    return Path(filepath).suffix.lower() in allowed_extensions


# individual upload_file_name checker
def validator(upload_file_name: str) -> tuple[bool, str]:
    # check that file_name is a string
    if not isinstance(upload_file_name, str):
        failure_message = "upload_file_name must be input as a string"
        print(failure_message)
        return False, failure_message

    # check that upload_file_name length is greater than 0
    if len(upload_file_name) == 0:
        failure_message = "invalid upload_file_name: length is 0"
        print(failure_message)
        return False, failure_message

    # check that upload_file_name length is less than 64
    if len(upload_file_name) > MAX_UPLOAD_FILE_NAME_LENGTH:
        failure_message = (
            f"invalid upload_file_name: length is greater than 64 (current maximum length allowable, which is {MAX_UPLOAD_FILE_NAME_LENGTH}"
        )
        print(failure_message)
        return False, failure_message

    # check is_valid_upload_file_name
    if not is_valid_upload_file_name(upload_file_name):
        failure_message = f"invalid upload_file_name: must match the regex pattern"
        return False, failure_message

    # check that upload_file_name ends with .mp4
    if not has_video_extension(upload_file_name):
        failure_message = f"invalid upload_file_name: must end with allowable extension {allowed_extensions}"
        return False, failure_message

    # success
    success_message = "success - upload_file_name passed validation"
    print(success_message)
    return True, success_message
