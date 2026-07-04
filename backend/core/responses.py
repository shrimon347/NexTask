"""Custom response wrappers for consistent API communication layouts.

Implements a predictable industry-standard layout mapping for every outcome across
successful workflows, schema validation traps, or unhandled runtime failures.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from rest_framework import status
from rest_framework.response import Response


class APIResponse:
    """Standardized production API response schema architect.

    Every method normalizes downstream payloads into a single, uniform layout contract:
    {
        "success": bool,
        "message": str,
        "data": Any,
        "errors": dict/list/str,
        "error_code": str/null,
        "meta": dict/null,
        "timestamp": str (ISO 8601 UTC format)
    }
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Request completed successfully.",
        status_code: int = status.HTTP_200_OK,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Constructs an RFC-compliant response representing positive runtime execution.

        Args:
            data: Main data object array, dictionary mapping, or structural entity payload.
            message: Clean string summarizing execution status updates for frontend tiers.
            status_code: Validated HTTP success status integer.
            meta: Optional auxiliary pagination metrics, context structures, or state fields.
        """
        response_payload: Dict[str, Any] = {
            "success": True,
            "message": message,
            "data": data,
            "errors": None,
            "error_code": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if meta is not None:
            response_payload["meta"] = meta

        return Response(data=response_payload, status=status_code)

    @staticmethod
    def error(
        message: str = "A transactional process boundary error occurred.",
        errors: Optional[Union[Dict[str, Any], List[Any], str]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: Optional[str] = None,
    ) -> Response:
        """Constructs an standardized failure payload capturing architectural anomalies.

        Args:
            message: A human-readable summary layout detailing execution roadblocks.
            errors: Precise machine-parsable tracking data (e.g., serializer error trees).
            status_code: Associated HTTP error category code mapping.
            error_code: Unique system code tracking categories (e.g., 'TOKEN_EXPIRED').
        """
        response_payload: Dict[str, Any] = {
            "success": False,
            "message": message,
            "data": None,
            "errors": errors if errors is not None else {},
            "error_code": error_code or "internal_application_error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return Response(data=response_payload, status=status_code)

    @staticmethod
    def created(
        data: Any = None,
        message: str = "Resource successfully instantiated.",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Convenience method generating HTTP 201 Created states."""
        return APIResponse.success(
            data=data, message=message, status_code=status.HTTP_201_CREATED, meta=meta
        )

    @staticmethod
    def no_content(
        message: str = "Resource tracking execution cleared successfully.",
    ) -> Response:
        """Convenience method generating HTTP 204 No Content states."""
        return APIResponse.success(
            data=None, message=message, status_code=status.HTTP_204_NO_CONTENT
        )

    @staticmethod
    def paginated(
        data: Any,
        page: int,
        page_size: int,
        total: int,
        message: str = "Paginated record query completed successfully.",
    ) -> Response:
        """Constructs an industry-standard structural layout for bulk data pagination.

        Args:
            data: Evaluated segment subset slice extracted from data persistence backends.
            page: Current targeted index page position marker.
            page_size: Volumetric density configuration tracking maximum payload layout constraints.
            total: Universal aggregate volume tracking integer matching search bounds.
            message: Summary phrase contextualizing bulk extractions.
        """
        calculated_total_pages = (
            (total + page_size - 1) // page_size if page_size > 0 else 0
        )

        meta_pagination_block = {
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_records": total,
                "total_pages": calculated_total_pages,
                "has_next": page * page_size < total,
                "has_previous": page > 1,
            }
        }

        return APIResponse.success(
            data=data, message=message, meta=meta_pagination_block
        )

    @staticmethod
    def validation_error(
        errors: Union[Dict[str, Any], List[Any], str],
        message: str = "Validation failed on the provided structural schema boundaries.",
    ) -> Response:
        """Generates HTTP 400 validation error responses."""
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="validation_error",
        )

    @staticmethod
    def unauthorized(
        message: str = "Authentication validation missing, rejected, or expired.",
        errors: Optional[Any] = None,
    ) -> Response:
        """Generates HTTP 401 unauthorized session responses."""
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="unauthorized_access",
        )

    @staticmethod
    def forbidden(
        message: str = "Privilege scope rules denied execution clearance on this resource pathway.",
        errors: Optional[Any] = None,
    ) -> Response:
        """Generates HTTP 403 authorization rule exception bounds responses."""
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="permission_denied",
        )

    @staticmethod
    def not_found(
        message: str = "The matching asset criteria index tracked zero references.",
        errors: Optional[Any] = None,
    ) -> Response:
        """Generates HTTP 404 entity omission exception responses."""
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="resource_not_found",
        )

    @staticmethod
    def conflict(
        message: str = "State alteration execution failed due to unique resource tracking data overlaps.",
        errors: Optional[Any] = None,
    ) -> Response:
        """Generates HTTP 409 multi-transaction state overlap collision responses."""
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_409_CONFLICT,
            error_code="resource_state_conflict",
        )

    @staticmethod
    def server_error(
        message: str = "An unhandled structural system failure occurred inside the network core.",
        errors: Optional[Any] = None,
    ) -> Response:
        """Generates HTTP 500 fatal process termination bounds responses."""
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="internal_server_error",
        )
