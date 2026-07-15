"""Mixins for project app."""

from .services import ProjectService


class ProjectServiceMixin:
    """Mixin to provide project service to views."""

    @property
    def project_service(self):
        """Lazy-load project service."""
        if not hasattr(self, "_project_service"):
            self._project_service = ProjectService()
        return self._project_service
