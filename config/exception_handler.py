import logging
import traceback

from rest_framework import status
from rest_framework.exceptions import (
    ErrorDetail,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken

logger = logging.getLogger("app_log")


class CustomExceptionHandler:
    """
    Custom Exception handler which have different methods
    which handles specific exceptions
    """

    def __init__(self, exc, content, drf_exception):
        self.exc = exc
        self.content = content
        self.response = {}
        self.drf_exception = drf_exception

    def validation_error(self):
        self.response.update(
            {
                "message": "Invalid data.",
                "errors": [flatten(self.drf_exception.data)],
                "status": "invalid_data",
            }
        )
        if self.drf_exception.data.get("data"):
            self.response.update({"data": [self.drf_exception.data.get("data")]})
        return self.response

    def invalid_token(self):
        self.response.update(
            {
                "message": "Invalid token.",
                "errors": [],
                "status": "invalid_token",
            }
        )
        return self.response

    def not_found(self):
        self.response.update(
            {
                "message": str(self.exc.detail),
                "errors": [],
                "status": self.exc.get_codes(),
            }
        )
        return self.response

    def not_authenticated(self):
        user_token = self.content.get("request").headers.get("token")
        if user_token:
            self.response.update(
                {
                    "message": "Unauthorized Customer",
                    "errors": [{"token": "Invalid Token"}],
                    "status": "unauthorized_customer",
                }
            )
        else:
            self.response.update(
                {
                    "message": "Not Authenticated.",
                    "errors": [
                        {
                            "authentication": "Authentication Credentials are not provided."
                        }
                    ],
                    "status": "not_authenticated",
                }
            )
        return self.response

    def internal_server_error(self):
        tb = traceback.format_exc()
        logger.error(f"Exception occurred: {str(self.exc)}\nTraceback: \n{tb}")
        self.response.update(
            {
                "message": "Internal Server Error.",
                "errors": [],
                "status": "internal_server_error",
            }
        )
        return self.response

    def permission_denied(self):
        self.response.update(
            {
                "message": "Permission Denied.",
                "errors": [{self.exc.get_codes(): self.exc.detail}],
                "status": self.exc.get_codes(),
            }
        )
        return self.response

    def unknown_error(self):
        self.response["message"] = self.exc.detail
        self.response["errors"] = [{self.exc.get_codes(): self.exc.detail}]

        return self.response

    def method_not_allowed(self):
        self.drf_exception.status_code = 404
        self.response.update(
            {
                "message": "Method Not Allowed.",
                "errors": [{self.exc.get_codes(): self.exc.detail}],
                "status": self.exc.get_codes(),
            }
        )
        return self.response


def new_customer_exception_handler(exc, content):
    """
        A custom exception handler that handles various
    types of exceptions and returns
    appropriate responses.
    Args:
        exc (Exception): The exception to be handled.
        context (dict): The context dictionary containing metadata about the request.

    Returns:
        Response: A response containing appropriate
          information about the exception.
    """
    drf_exception = exception_handler(exc, content)
    exception_handler_instance = CustomExceptionHandler(
        exc=exc, content=content, drf_exception=drf_exception
    )
    if drf_exception is not None:
        # exception map which have different exception mapped
        exception_map = {
            ValidationError: exception_handler_instance.validation_error,
            InvalidToken: exception_handler_instance.invalid_token,
            AuthenticationFailed: exception_handler_instance.invalid_token,
            NotAuthenticated: exception_handler_instance.not_authenticated,
            PermissionDenied: exception_handler_instance.permission_denied,
            NotFound: exception_handler_instance.not_found,
            MethodNotAllowed: exception_handler_instance.method_not_allowed,
        }
        if not exception_map.get(exc.__class__):
            # run unknown_error() method if the exception is not registered
            drf_exception.data = exception_handler_instance.unknown_error()
            return drf_exception
        # run the specific exception handler method
        drf_exception.data = exception_map[exc.__class__]()
        return drf_exception
    # if any issue occurs run internal_server_error() method
    return Response(
        exception_handler_instance.internal_server_error(),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def flatten(data):
    """
    Flatten a dictionary with nested lists or
    dictionaries and return a flattened dictionary
    with a specific format that combines all
    error messages in one level and removes the outer parent key.

    Args:
    data (dict): The dictionary to flatten.

    Returns:
    dict: The flattened dictionary.
    """
    flattened_data = {}
    for key, value in data.items():
        if isinstance(value, dict):
            # Recursively flatten any nested dictionaries.
            flattened_value = flatten(value)
            for nested_key, nested_value in flattened_value.items():
                flattened_data[nested_key] = nested_value
        elif isinstance(value, list):
            # Flatten any nested lists of dictionaries.
            for item in value:
                if isinstance(item, dict):
                    flattened_item = flatten(item)
                    for nested_key, nested_value in flattened_item.items():
                        flattened_data[nested_key] = nested_value
                elif isinstance(item, ErrorDetail):
                    # If the item is an ErrorDetail object, extract the error message.
                    flattened_data[key] = item
    return flattened_data
