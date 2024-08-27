import re


def validator(hash_string: str) -> tuple[bool, str]:
    if not isinstance(hash_string, str):
        failure_message = "failure - input hash_string is not a string"
        return False, failure_message
    if len(hash_string) != 64:
        fail_message = f"FAILURE: hash invalid length - {len(hash_string)} - must be length 64"
        return False, fail_message
    hex_pattern = re.compile(r"^[0-9a-fA-F]{64}$")
    fail_message = "FAILURE: hash failed regex check"
    if not bool(hex_pattern.match(hash_string)):
        return False, fail_message
    return True, "SUCCESS: hash passed validator"
