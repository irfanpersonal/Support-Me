from email_validator import validate_email

def isValidEmail(value: str) -> bool:
    try:
        valid = validate_email(value)
        return valid
    except Exception:
        return False