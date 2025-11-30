from rest_framework.exceptions import APIException


class CustomValidationException(APIException):
    status_code = 400
    default_detail = "Invalid input."
    default_code = "invalid"


__all__ = ["CustomValidationException"]
