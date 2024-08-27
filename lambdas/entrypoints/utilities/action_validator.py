valid_actions = ["upload", "upload_test"]


def validator(action: str) -> tuple[bool, str]:
    # validate action
    if action not in valid_actions:
        failure_message = "action not 'upload' or 'upload_test'"
        print(failure_message)
        return False, failure_message
    message = "success - action validated"
    return True, message
