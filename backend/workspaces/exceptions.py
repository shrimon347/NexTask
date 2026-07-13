"""Custom exceptions for workspace app."""


class WorkspaceNotFound(Exception):
    """Raised when a workspace is not found."""

    pass


class WorkspacePermissionDenied(Exception):
    """Raised when user lacks permission for workspace operation."""

    pass


class WorkspaceMemberNotFound(Exception):
    """Raised when a workspace member is not found."""

    pass
