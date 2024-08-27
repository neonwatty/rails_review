from entrypoints.utilities.action_validator import validator as action_validate
from entrypoints.utilities.upload_file_name_validator import validator as upload_file_name_validate
from entrypoints.utilities.file_type_validator import validator as file_type_validate
from entrypoints.utilities.file_hash_validator import validator as file_hash_validate


def validator(action: str, file_data: str, file_type: str, file_hash: str) -> tuple[bool, str]:
    # validate action
    a_check, a_message = action_validate(action)
    if a_check is False:
        return a_check, a_message

    # validate upload_file_name
    if "upload" in action:
        fn_check, fn_message = upload_file_name_validate(file_data)
        if fn_check is False:
            return fn_check, fn_message

    # validate file_type
    ft_check, ft_message = file_type_validate(file_type)
    if ft_check is False:
        return ft_check, ft_message

    # check file hash
    fh_check, fh_message = file_hash_validate(file_hash)
    if fh_check is False:
        return fh_check, fh_message

    # return success
    success_message = "SUCCESS: payload passed validators"
    print(success_message)
    return True, success_message
