"""Custom exception classes for the application layer.

All specialized custom exceptions subclass `BaseAPIException` (which extends
Django REST Framework's native `APIException`) to guarantee a uniform error
response payload shape, automated telemetry hooks, and consistent HTTP status mapping.

Typical usage example:
    from core.exceptions import NotFoundError, ValidationError

    if not product_exists:
        raise NotFoundError(detail="Product item missing.")
"""

from typing import Any, Dict, Optional, Union

from rest_framework import status
from rest_framework.exceptions import APIException


class BaseAPIException(APIException):
    """Abstract baseline exception class acting as the root anchor for all API errors.

    Extends DRF's `APIException` to normalize structural attributes across
    the framework. It enables contextual state passing through optional payloads.

    Attributes:
        status_code (int): Target RFC-compliant HTTP status response code.
        default_detail (str): Human-readable fallback message displayed to end-users.
        default_code (str): Machine-readable programmatic classification string token.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail: str = "An unexpected server-side runtime error occurred."
    default_code: str = "internal_server_error"

    def __init__(
        self,
        detail: Optional[Union[str, Dict[str, Any], list]] = None,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initializes structural error properties and triggers DRF's core construction.

        Args:
            detail: Descriptive error context (string message or nested schema dict).
            code: Unique programmatic token identifying the root exception flavor.
            status_code: Runtime status integer used to override class definition states.
            extra_payload: Dictionary container mapping debugging tracking keys.
        """
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        if status_code is not None:
            self.status_code = status_code

        self.extra_payload: Optional[Dict[str, Any]] = extra_payload
        super().__init__(detail, code)


class ValidationError(BaseAPIException):
    """Exception raised when an inbound request fails semantic or structural format rules.

    Use Case:
        Triggered when JSON payloads contain field data type mismatches, missing
        properties, or invalid validation schema constraints.

    API Response Target:
        HTTP 400 Bad Request
    """

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_detail: str = "The request payload failed structural validation checks."
    default_code: str = "validation_error"


class AuthenticationError(BaseAPIException):
    """Exception raised when identifying credentials are missing, invalid, or expired.

    Use Case:
        Triggered when bearer JSON Web Tokens (JWT) fail signatures, expire, or when
        login transaction operations supply mismatching key sets.

    API Response Target:
        HTTP 401 Unauthorized
    """

    status_code: int = status.HTTP_401_UNAUTHORIZED
    default_detail: str = (
        "Authentication credentials were missing, expired, or invalid."
    )
    default_code: str = "authentication_error"


class PermissionDenied(BaseAPIException):
    """Exception raised when authenticated identities lack explicit authorization scopes.

    Use Case:
        Triggered when an authenticated entity attempts to mutate assets restricted by
        Role-Based Access Control (RBAC) tiers (e.g., standard users accessing admin views).

    API Response Target:
        HTTP 403 Forbidden
    """

    status_code: int = status.HTTP_403_FORBIDDEN
    default_detail: str = (
        "Your security scope lacks required privileges for this action."
    )
    default_code: str = "permission_denied"


class NotFound(BaseAPIException):
    """Exception raised when the targeted tracking reference entity cannot be resolved.

    Use Case:
        Triggered when database unique UUID mappings, numeric indexes, or target system
        filepath routes return completely empty transaction states.

    API Response Target:
        HTTP 404 Not Found
    """

    status_code: int = status.HTTP_404_NOT_FOUND
    default_detail: str = "The requested entity instance could not be located."
    default_code: str = "not_found"


class ConflictError(BaseAPIException):
    """Exception raised during state mutation attempts that break asset uniqueness.

    Use Case:
        Triggered when registration engines detect existing identical phone strings or
        unique database constraint records.

    API Response Target:
        HTTP 409 Conflict
    """

    status_code: int = status.HTTP_409_CONFLICT
    default_detail: str = "The request state conflicts with existing database records."
    default_code: str = "conflict_error"


class BusinessLogicError(BaseAPIException):
    """Exception raised when payload inputs are well-formed but break business domain invariants.

    Use Case:
        Triggered when processing bank transfers where requested credit withdrawal blocks
        exceed active account balances, or scheduling appointments on past calendars.

    API Response Target:
        HTTP 422 Unprocessable Entity
    """

    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail: str = (
        "The operational target state violates business logic invariants."
    )
    default_code: str = "business_logic_error"


class RateLimitExceeded(BaseAPIException):
    """Exception raised when API endpoint access frequencies break volumetric allocation ceilings.

    Use Case:
        Triggered by middleware throttling architectures when high-velocity spam hitting
        sensitive authentication pathways requires a temporary blocking state.

    API Response Target:
        HTTP 429 Too Many Requests
    """

    status_code: int = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail: str = (
        "API transactional volumetric thresholds exceeded. Please delay retry loops."
    )
    default_code: str = "rate_limit_exceeded"


class ServiceUnavailable(BaseAPIException):
    """Exception raised when critical application dependencies are administratively down.

    Use Case:
        Triggered during deployment windows when background caching networks (Redis) or
        asynchronous worker pipelines go offline temporarily.

    API Response Target:
        HTTP 503 Service Unavailable
    """

    status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail: str = (
        "The target application engine tier is temporarily unavailable."
    )
    default_code: str = "service_unavailable"


class DatabaseError(BaseAPIException):
    """Exception raised when atomic database layers crash or fail execution loops.

    Use Case:
        Triggered by deadlock events, database transaction isolation rollbacks,
        or sudden driver network dropouts during active queries.

    API Response Target:
        HTTP 500 Internal Server Error
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail: str = "An internal database persistence failure occurred."
    default_code: str = "database_error"


class ExternalServiceError(BaseAPIException):
    """Exception raised when third-party cloud gateways return failure responses.

    Use Case:
        Triggered when external vendor microservices (e.g., Stripe payment processing,
        Twilio SMS message dispatch) timeout or return fatal 5xx errors.

    API Response Target:
        HTTP 502 Bad Gateway
    """

    status_code: int = status.HTTP_502_BAD_GATEWAY
    default_detail: str = (
        "An upstream partner application interface returned a fatal state."
    )
    default_code: str = "external_service_error"
