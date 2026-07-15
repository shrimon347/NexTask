"""Workspace-specific exceptions built on top of global API exceptions."""

from core.exceptions import NotFound, PermissionDenied


class WorkspaceNotFound(NotFound):
    """Raised when a workspace is not found."""

    default_detail = "The requested workspace could not be found."
    default_code = "workspace_not_found"


class WorkspacePermissionDenied(PermissionDenied):
    """Raised when user lacks permission for workspace operation."""

    default_detail = "You do not have permission to perform this workspace action."
    default_code = "workspace_permission_denied"


class WorkspaceMemberNotFound(NotFound):
    """Raised when a workspace member is not found."""

    default_detail = "The requested workspace member could not be found."
    default_code = "workspace_member_not_found"
