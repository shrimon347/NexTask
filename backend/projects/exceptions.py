from core.exceptions import NotFound, PermissionDenied


class ProjectNotFound(NotFound):
    """Raised when a project is not found."""

    pass


class ProjectPermissionDenied(PermissionDenied):
    """Raised when user lacks permission for project operation."""

    pass


class ProjectMemberNotFound(NotFound):
    """Raised when a project member is not found."""

    pass
