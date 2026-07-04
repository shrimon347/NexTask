# core/exception_handler.py
"""Centralized exception handling routing intercepting error cascades into standardized responses."""

import logging
from typing import Any, Dict

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoDatabaseValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as native_drf_exception_handler

from .exceptions import BaseAPIException
from .responses import APIResponse

application_server_error_logger = logging.getLogger("django.request")
security_rate_limit_metrics_logger = logging.getLogger("security")


def global_api_exception_handler(exc: Exception, context: Dict[str, Any]) -> Response:
    """Catches exceptions across the DRF routing mesh and forces them into APIResponse contracts."""

    # Check if native DRF engine identifies the error layout first
    drf_pre_processed_response = native_drf_exception_handler(exc, context)

    active_request = context.get("request")
    endpoint_route = active_request.path if active_request else "UNKNOWN_ROUTE"
    client_ip = (
        active_request.META.get("REMOTE_ADDR", "UNKNOWN_IP")
        if active_request
        else "UNKNOWN_IP"
    )
    user_id = (
        getattr(active_request.user, "id", "AnonymousUser")
        if active_request and hasattr(active_request, "user")
        else "AnonymousUser"
    )

    # CASE 1: Catch custom project APIException instances
    if isinstance(exc, BaseAPIException):
        if exc.status_code == 429:
            security_rate_limit_metrics_logger.warning(
                f"[SECURITY VOLUMETRIC THROTTLE] Route: {endpoint_route} | IP: {client_ip} | Account: {user_id}"
            )

        return APIResponse.error(
            message=str(exc.detail),
            errors=getattr(exc, "extra_payload", None),
            status_code=exc.status_code,
            error_code=exc.get_codes(),
        )

    # CASE 2: Catch core underlying Django database layer omissions
    if isinstance(exc, ObjectDoesNotExist):
        return APIResponse.not_found(
            message="The requested object does not exist within the persistence system indices."
        )

    if isinstance(exc, DjangoDatabaseValidationError):
        return APIResponse.validation_error(
            message="Data format constraints rejected by schema rules.",
            errors=getattr(exc, "message_dict", str(exc)),
        )

    # CASE 3: Standardize unhandled built-in DRF exceptions (like 405 Method Not Allowed)
    if drf_pre_processed_response is not None:
        return APIResponse.error(
            message=drf_pre_processed_response.data.get(
                "detail", "An explicit API error occurred."
            ),
            errors=drf_pre_processed_response.data,
            status_code=drf_pre_processed_response.status_code,
            error_code=getattr(exc, "default_code", "api_framework_error"),
        )

    # CASE 4: The Uncaught System Fallback Crash (Divided by Zero, KeyError, etc.)
    application_server_error_logger.error(
        f"[CRITICAL APPLICATION SERVER FAULT] Route: {endpoint_route} | User: {user_id} | Exception: {str(exc)}",
        exc_info=True,
    )

    return APIResponse.server_error(
        message="An unexpected system crash occurred. Core engineering metrics have been generated."
    )
