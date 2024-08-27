valid_file_types = ["video/mp4"]


def validator(file_type: str) -> tuple[bool, str]:
    if not isinstance(file_type, str):
        failure_message = "failure - input file_type is not a string"
        return False, failure_message
    if file_type not in valid_file_types:
        failure_message = "failure - file_type is incorrect"
        return False, failure_message
    return True, "success - file_type validated successfully"
