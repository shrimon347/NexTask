"""Mixins for workspace app."""

from .services import WorkspaceService


class WorkspaceServiceMixin:
    """Mixin to provide workspace service to views."""

    @property
    def workspace_service(self):
        """Lazy-load workspace service."""
        if not hasattr(self, "_workspace_service"):
            self._workspace_service = WorkspaceService()
        return self._workspace_service
