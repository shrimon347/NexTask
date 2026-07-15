# views/project_views.py
import logging

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.exceptions import ValidationError
from core.responses import APIResponse

from .exceptions import ProjectMemberNotFound, ProjectNotFound, ProjectPermissionDenied
from .mixins import ProjectServiceMixin
from .serializers import (
    ProjectArchiveSerializer,
    ProjectCreateSerializer,
    ProjectDetailSerializer,
    ProjectListQuerySerializer,
    ProjectListSerializer,
    ProjectMemberAddSerializer,
    ProjectMemberRemoveSerializer,
    ProjectMemberUpdateRoleSerializer,
    ProjectMemberUpdateTagsSerializer,
    ProjectProgressUpdateSerializer,
    ProjectStatusUpdateSerializer,
    ProjectUpdateSerializer,
)

logger = logging.getLogger(__name__)


class ProjectListCreateView(ProjectServiceMixin, APIView):
    """
    Project list and create endpoint.

    GET /api/v1/workspaces/{workspace_id}/projects/
    POST /api/v1/workspaces/{workspace_id}/projects/

    GET Query Parameters:
        - status: Filter by project status (optional)
        - is_archived: Filter by archive status (optional, default: show active only)
        - search: Search by title or description (optional)
        - sort_by: Sort field (created_at, due_date, title, progress)
        - sort_order: Sort direction (asc, desc)

    POST Request Body:
        {
            "title": "My Project",
            "description": "Optional description",
            "status": "planning",
            "start_date": "2024-01-01",
            "due_date": "2024-12-31",
            "progress": 0
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="projects_list",
        summary="List Projects",
        description="List all projects in a workspace. Results include user's role and member count. Supports filtering and sorting.",
        parameters=[
            OpenApiParameter(
                name="status",
                description="Filter by project status",
                required=False,
                type=str,
                enum=["planning", "in_progress", "on_hold", "completed", "cancelled"],
            ),
            OpenApiParameter(
                name="is_archived",
                description="Filter by archive status. If not provided, shows active projects only.",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="search",
                description="Search projects by title or description",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="sort_by",
                description="Sort field (default: created_at)",
                required=False,
                type=str,
                enum=["created_at", "due_date", "title", "progress"],
            ),
            OpenApiParameter(
                name="sort_order",
                description="Sort direction (default: desc)",
                required=False,
                type=str,
                enum=["asc", "desc"],
            ),
        ],
        responses={
            200: ProjectListSerializer(many=True),
            400: OpenApiResponse(description="Invalid query parameters"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Not a workspace member"),
            404: OpenApiResponse(description="Workspace not found"),
        },
        tags=["Projects"],
    )
    def get(self, request, workspace_id):
        """
        Handle project list request.

        Returns filtered and sorted list of projects in a workspace.
        """
        logger.info(
            "Project list request from user: %s, workspace: %s",
            request.user.email,
            workspace_id,
        )

        # Validate query parameters
        query_serializer = ProjectListQuerySerializer(data=request.query_params)

        if not query_serializer.is_valid():
            errors = self._format_serializer_errors(query_serializer.errors)
            logger.warning(
                "Project list query validation failed for user %s. Errors: %s",
                request.user.email,
                errors,
            )
            return APIResponse.validation_error(
                message="Invalid query parameters", errors=errors
            )

        # Extract validated query params
        validated_data = query_serializer.validated_data

        # Delegate to service layer
        try:
            projects = self.project_service.list_projects(
                user=request.user,
                workspace_id=workspace_id,
                status=validated_data.get("status"),
                is_archived=validated_data.get("is_archived"),
                search=validated_data.get("search"),
                sort_by=validated_data.get("sort_by", "created_at"),
                sort_order=validated_data.get("sort_order", "desc"),
            )

            # Serialize response
            response_serializer = ProjectListSerializer(projects, many=True)

            logger.info(
                "Projects retrieved successfully for user %s. Workspace: %s, Count: %d",
                request.user.email,
                workspace_id,
                len(projects),
            )

            return APIResponse.success(
                message="Projects retrieved successfully",
                data=response_serializer.data,
            )

        except ProjectPermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on workspace %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.forbidden(message=str(e))

        except Exception as e:
            logger.error(
                "Unexpected error during project list for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while retrieving projects"
            )

    @extend_schema(
        operation_id="projects_create",
        summary="Create Project",
        description="Create a new project in a workspace. The authenticated user automatically becomes the project manager.",
        request=ProjectCreateSerializer,
        responses={
            201: ProjectDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Not a workspace member"),
            404: OpenApiResponse(description="Workspace not found"),
            409: OpenApiResponse(description="Conflict - Project title already exists"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Projects"],
    )
    def post(self, request, workspace_id):
        """Handle project creation request."""
        logger.info(
            "Project creation request from user: %s, workspace: %s",
            request.user.email,
            workspace_id,
        )

        # Validate request data
        serializer = ProjectCreateSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Project creation validation failed for user %s. Errors: %s",
                request.user.email,
                errors,
            )
            return APIResponse.validation_error(
                message="Validation failed", errors=errors
            )

        # Extract validated data
        validated_data = serializer.validated_data

        # Delegate to service layer
        try:
            project_data = self.project_service.create_project(
                user=request.user,
                workspace_id=workspace_id,
                title=validated_data["title"],
                description=validated_data.get("description", ""),
                status=validated_data.get("status", "planning"),
                start_date=validated_data.get("start_date"),
                due_date=validated_data.get("due_date"),
                progress=validated_data.get("progress", 0),
            )

            # Serialize response
            response_serializer = ProjectDetailSerializer(project_data)

            logger.info(
                "Project created successfully. ID: %s, User: %s",
                project_data.get("id"),
                request.user.email,
            )

            return APIResponse.created(
                message="Project created successfully",
                data=response_serializer.data,
            )

        except ProjectPermissionDenied as e:
            logger.warning(
                "Project creation failed for user %s. Error: %s",
                request.user.email,
                str(e),
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning(
                "Project creation failed for user %s. Error: %s",
                request.user.email,
                str(e),
            )
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during project creation for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while creating the project"
            )

    def _format_serializer_errors(self, errors):
        """Format serializer errors to a flat dictionary."""
        formatted = {}
        for field, messages in errors.items():
            if isinstance(messages, list):
                formatted[field] = messages[0] if messages else "Invalid value"
            else:
                formatted[field] = str(messages)
        return formatted


class ProjectDetailView(ProjectServiceMixin, APIView):
    """
    Project detail, update, and delete endpoint.

    GET /api/v1/projects/{project_id}/
    PATCH /api/v1/projects/{project_id}/
    DELETE /api/v1/projects/{project_id}/
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="projects_retrieve",
        summary="Get Project Details",
        description="Retrieve detailed project information including all members with their roles and tags.",
        responses={
            200: ProjectDetailSerializer,
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Not a project member"),
            404: OpenApiResponse(description="Project not found"),
        },
        tags=["Projects"],
    )
    def get(self, request, project_id):
        """Handle project detail retrieval request."""
        logger.info(
            "Project detail request from user: %s, project_id: %s",
            request.user.email,
            project_id,
        )

        try:
            project_data = self.project_service.get_project_details(
                user=request.user,
                project_id=project_id,
            )

            # Serialize response
            response_serializer = ProjectDetailSerializer(project_data)

            return APIResponse.success(
                message="Project details retrieved successfully",
                data=response_serializer.data,
            )

        except ProjectNotFound as e:
            logger.warning(
                "Project not found for user %s. ID: %s",
                request.user.email,
                project_id,
            )
            return APIResponse.not_found(message=str(e))

        except ProjectPermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on project %s",
                request.user.email,
                project_id,
            )
            return APIResponse.forbidden(message=str(e))

        except Exception as e:
            logger.error(
                "Unexpected error during project retrieval for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while retrieving the project"
            )

    @extend_schema(
        operation_id="projects_update",
        summary="Update Project",
        description="Update project details. Only project managers or workspace admins can update. At least one field must be provided.",
        request=ProjectUpdateSerializer,
        responses={
            200: ProjectDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Project not found"),
            409: OpenApiResponse(description="Conflict - Project title already exists"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Projects"],
    )
    def patch(self, request, project_id):
        """Handle project update request."""
        logger.info(
            "Project update request from user: %s, project_id: %s",
            request.user.email,
            project_id,
        )

        # Validate request data
        serializer = ProjectUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Project update validation failed for user %s. Errors: %s",
                request.user.email,
                errors,
            )
            return APIResponse.validation_error(
                message="Validation failed", errors=errors
            )

        # Extract validated data
        validated_data = serializer.validated_data

        # Delegate to service layer
        try:
            project_data = self.project_service.update_project(
                user=request.user,
                project_id=project_id,
                **validated_data,
            )

            # Serialize response
            response_serializer = ProjectDetailSerializer(project_data)

            logger.info(
                "Project updated successfully. ID: %s, User: %s",
                project_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Project updated successfully",
                data=response_serializer.data,
            )

        except ProjectNotFound as e:
            logger.warning(
                "Project not found for user %s. ID: %s",
                request.user.email,
                project_id,
            )
            return APIResponse.not_found(message=str(e))

        except ProjectPermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on project %s",
                request.user.email,
                project_id,
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning(
                "Project update failed for user %s. Error: %s",
                request.user.email,
                str(e),
            )
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during project update for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while updating the project"
            )

    @extend_schema(
        operation_id="projects_delete",
        summary="Delete Project",
        description="Permanently delete a project. Only workspace owners or the project creator can delete. This action is irreversible.",
        responses={
            200: OpenApiResponse(description="Project deleted successfully"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Project not found"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Projects"],
    )
    def delete(self, request, project_id):
        """Handle project deletion request."""
        logger.info(
            "Project deletion request from user: %s, project_id: %s",
            request.user.email,
            project_id,
        )

        try:
            self.project_service.delete_project(
                user=request.user,
                project_id=project_id,
            )

            logger.info(
                "Project deleted successfully. ID: %s, User: %s",
                project_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Project deleted successfully",
                data=None,
            )

        except ProjectNotFound as e:
            logger.warning(
                "Project not found for user %s. ID: %s",
                request.user.email,
                project_id,
            )
            return APIResponse.not_found(message=str(e))

        except ProjectPermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on project %s",
                request.user.email,
                project_id,
            )
            return APIResponse.forbidden(message=str(e))

        except Exception as e:
            logger.error(
                "Unexpected error during project deletion for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while deleting the project"
            )

    def _format_serializer_errors(self, errors):
        """Format serializer errors to a flat dictionary."""
        formatted = {}
        for field, messages in errors.items():
            if isinstance(messages, list):
                formatted[field] = messages[0] if messages else "Invalid value"
            else:
                formatted[field] = str(messages)
        return formatted


class ProjectStatusUpdateView(ProjectServiceMixin, APIView):
    """
    Update project status endpoint.

    PATCH /api/v1/projects/{project_id}/status/

    Request Body:
        {
            "status": "in_progress"
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="projects_update_status",
        summary="Update Project Status",
        description="Update project status. Auto-updates progress for certain statuses (completed=100%, planning=0%).",
        request=ProjectStatusUpdateSerializer,
        responses={
            200: ProjectDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Project not found"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Projects"],
    )
    def patch(self, request, project_id):
        """Handle project status update request."""
        logger.info(
            "Project status update request from user: %s, project_id: %s",
            request.user.email,
            project_id,
        )

        # Validate request data
        serializer = ProjectStatusUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Status update validation failed for user %s. Errors: %s",
                request.user.email,
                errors,
            )
            return APIResponse.validation_error(
                message="Validation failed", errors=errors
            )

        # Delegate to service layer
        try:
            project_data = self.project_service.update_status(
                user=request.user,
                project_id=project_id,
                new_status=serializer.validated_data["status"],
            )

            # Serialize response
            response_serializer = ProjectDetailSerializer(project_data)

            logger.info(
                "Project status updated successfully. ID: %s, User: %s",
                project_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Project status updated successfully",
                data=response_serializer.data,
            )

        except ProjectNotFound as e:
            logger.warning(
                "Project not found for user %s. ID: %s",
                request.user.email,
                project_id,
            )
            return APIResponse.not_found(message=str(e))

        except ProjectPermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on project %s",
                request.user.email,
                project_id,
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning(
                "Status update failed for user %s. Error: %s",
                request.user.email,
                str(e),
            )
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during status update for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while updating the project status"
            )

    def _format_serializer_errors(self, errors):
        """Format serializer errors to a flat dictionary."""
        formatted = {}
        for field, messages in errors.items():
            if isinstance(messages, list):
                formatted[field] = messages[0] if messages else "Invalid value"
            else:
                formatted[field] = str(messages)
        return formatted


class ProjectProgressUpdateView(ProjectServiceMixin, APIView):
    """
    Update project progress endpoint.

    PATCH /api/v1/projects/{project_id}/progress/

    Request Body:
        {
            "progress": 75
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="projects_update_progress",
        summary="Update Project Progress",
        description="Update project progress percentage (0-100). Only managers, contributors, or workspace admins can update.",
        request=ProjectProgressUpdateSerializer,
        responses={
            200: ProjectDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Project not found"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Projects"],
    )
    def patch(self, request, project_id):
        """Handle project progress update request."""
        logger.info(
            "Project progress update request from user: %s, project_id: %s",
            request.user.email,
            project_id,
        )

        # Validate request data
        serializer = ProjectProgressUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Progress update validation failed for user %s. Errors: %s",
                request.user.email,
                errors,
            )
            return APIResponse.validation_error(
                message="Validation failed", errors=errors
            )

        # Delegate to service layer
        try:
            project_data = self.project_service.update_progress(
                user=request.user,
                project_id=project_id,
                progress=serializer.validated_data["progress"],
            )

            # Serialize response
            response_serializer = ProjectDetailSerializer(project_data)

            logger.info(
                "Project progress updated successfully. ID: %s, User: %s",
                project_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Project progress updated successfully",
                data=response_serializer.data,
            )

        except ProjectNotFound as e:
            logger.warning(
                "Project not found for user %s. ID: %s",
                request.user.email,
                project_id,
            )
            return APIResponse.not_found(message=str(e))

        except ProjectPermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on project %s",
                request.user.email,
                project_id,
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning(
                "Progress update failed for user %s. Error: %s",
                request.user.email,
                str(e),
            )
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during progress update for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while updating the project progress"
            )

    def _format_serializer_errors(self, errors):
        """Format serializer errors to a flat dictionary."""
        formatted = {}
        for field, messages in errors.items():
            if isinstance(messages, list):
                formatted[field] = messages[0] if messages else "Invalid value"
            else:
                formatted[field] = str(messages)
        return formatted


class ProjectArchiveView(ProjectServiceMixin, APIView):
    """
    Archive/unarchive project endpoint.

    PATCH /api/v1/projects/{project_id}/archive/

    Request Body:
        {
            "is_archived": true
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="projects_toggle_archive",
        summary="Archive/Unarchive Project",
        description="Archive or unarchive a project. Archived projects are hidden from default list views.",
        request=ProjectArchiveSerializer,
        responses={
            200: ProjectDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Project not found"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Projects"],
    )
    def patch(self, request, project_id):
        """Handle project archive/unarchive request."""
        logger.info(
            "Project archive request from user: %s, project_id: %s",
            request.user.email,
            project_id,
        )

        # Validate request data
        serializer = ProjectArchiveSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Archive validation failed for user %s. Errors: %s",
                request.user.email,
                errors,
            )
            return APIResponse.validation_error(
                message="Validation failed", errors=errors
            )

        # Delegate to service layer
        try:
            project_data = self.project_service.toggle_archive(
                user=request.user,
                project_id=project_id,
                is_archived=serializer.validated_data["is_archived"],
            )

            # Serialize response
            response_serializer = ProjectDetailSerializer(project_data)

            logger.info(
                "Project %s successfully. ID: %s, User: %s",
                (
                    "archived"
                    if serializer.validated_data["is_archived"]
                    else "unarchived"
                ),
                project_id,
                request.user.email,
            )

            return APIResponse.success(
                message=f"Project {'archived' if serializer.validated_data['is_archived'] else 'unarchived'} successfully",
                data=response_serializer.data,
            )

        except ProjectNotFound as e:
            logger.warning(
                "Project not found for user %s. ID: %s",
                request.user.email,
                project_id,
            )
            return APIResponse.not_found(message=str(e))

        except ProjectPermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on project %s",
                request.user.email,
                project_id,
            )
            return APIResponse.forbidden(message=str(e))

        except Exception as e:
            logger.error(
                "Unexpected error during archive toggle for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while updating the project archive status"
            )

    def _format_serializer_errors(self, errors):
        """Format serializer errors to a flat dictionary."""
        formatted = {}
        for field, messages in errors.items():
            if isinstance(messages, list):
                formatted[field] = messages[0] if messages else "Invalid value"
            else:
                formatted[field] = str(messages)
        return formatted


class ProjectMemberAddView(ProjectServiceMixin, APIView):
    """
    Add member to project endpoint.

    POST /api/v1/projects/{project_id}/members/add/

    Request Body:
        {
            "user_id": "uuid",
            "role": "contributor",
            "tags": ["frontend", "lead"]
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="projects_add_member",
        summary="Add Project Member",
        description="Add a new member to project. User must be a workspace member first.",
        request=ProjectMemberAddSerializer,
        responses={
            200: ProjectDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Project or user not found"),
            409: OpenApiResponse(description="Conflict - User already a member"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Project Members"],
    )
    def post(self, request, project_id):
        """Handle add member request."""
        logger.info(
            "Add member request from user: %s, project_id: %s",
            request.user.email,
            project_id,
        )

        # Validate request data
        serializer = ProjectMemberAddSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Add member validation failed for user %s. Errors: %s",
                request.user.email,
                errors,
            )
            return APIResponse.validation_error(
                message="Validation failed", errors=errors
            )

        # Delegate to service layer
        try:
            project_data = self.project_service.add_member(
                user=request.user,
                project_id=project_id,
                member_id=serializer.validated_data["user_id"],
                role=serializer.validated_data.get("role", "contributor"),
                tags=serializer.validated_data.get("tags", []),
            )

            # Serialize response
            response_serializer = ProjectDetailSerializer(project_data)

            logger.info(
                "Member added successfully. Project: %s, By: %s",
                project_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Member added successfully",
                data=response_serializer.data,
            )

        except ProjectNotFound as e:
            logger.warning("Project not found. ID: %s", project_id)
            return APIResponse.not_found(message=str(e))

        except ProjectMemberNotFound as e:
            logger.warning("User not found for member addition.")
            return APIResponse.not_found(message=str(e))

        except ProjectPermissionDenied as e:
            logger.warning(
                "Permission denied for user %s to add member to project %s",
                request.user.email,
                project_id,
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning("Add member failed. Error: %s", str(e))
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during add member for project %s. Error: %s",
                project_id,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while adding the member"
            )

    def _format_serializer_errors(self, errors):
        """Format serializer errors to a flat dictionary."""
        formatted = {}
        for field, messages in errors.items():
            if isinstance(messages, list):
                formatted[field] = messages[0] if messages else "Invalid value"
            else:
                formatted[field] = str(messages)
        return formatted


class ProjectMemberRemoveView(ProjectServiceMixin, APIView):
    """
    Remove member from project endpoint.

    POST /api/v1/projects/{project_id}/members/remove/

    Request Body:
        {
            "user_id": "uuid"
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="projects_remove_member",
        summary="Remove Project Member",
        description="Remove a member from project. Members can remove themselves (leave). Cannot remove the last manager.",
        request=ProjectMemberRemoveSerializer,
        responses={
            200: ProjectDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Project or member not found"),
            409: OpenApiResponse(description="Conflict - Cannot remove last manager"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Project Members"],
    )
    def post(self, request, project_id):
        """Handle remove member request."""
        logger.info(
            "Remove member request from user: %s, project_id: %s",
            request.user.email,
            project_id,
        )

        # Validate request data
        serializer = ProjectMemberRemoveSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Remove member validation failed for user %s. Errors: %s",
                request.user.email,
                errors,
            )
            return APIResponse.validation_error(
                message="Validation failed", errors=errors
            )

        # Delegate to service layer
        try:
            project_data = self.project_service.remove_member(
                user=request.user,
                project_id=project_id,
                member_id=serializer.validated_data["user_id"],
            )

            # Serialize response
            response_serializer = ProjectDetailSerializer(project_data)

            logger.info(
                "Member removed successfully. Project: %s, By: %s",
                project_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Member removed successfully",
                data=response_serializer.data,
            )

        except ProjectNotFound as e:
            logger.warning("Project not found. ID: %s", project_id)
            return APIResponse.not_found(message=str(e))

        except ProjectMemberNotFound as e:
            logger.warning("Member not found in project %s.", project_id)
            return APIResponse.not_found(message=str(e))

        except ProjectPermissionDenied as e:
            logger.warning(
                "Permission denied for user %s to remove member from project %s",
                request.user.email,
                project_id,
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning("Remove member failed. Error: %s", str(e))
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during remove member for project %s. Error: %s",
                project_id,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while removing the member"
            )

    def _format_serializer_errors(self, errors):
        """Format serializer errors to a flat dictionary."""
        formatted = {}
        for field, messages in errors.items():
            if isinstance(messages, list):
                formatted[field] = messages[0] if messages else "Invalid value"
            else:
                formatted[field] = str(messages)
        return formatted


class ProjectMemberUpdateRoleView(ProjectServiceMixin, APIView):
    """
    Update member role endpoint.

    PATCH /api/v1/projects/{project_id}/members/role/

    Request Body:
        {
            "user_id": "uuid",
            "role": "manager"
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="projects_update_member_role",
        summary="Update Member Role",
        description="Update a member's role in project. Cannot demote the last manager.",
        request=ProjectMemberUpdateRoleSerializer,
        responses={
            200: ProjectDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Project or member not found"),
            409: OpenApiResponse(description="Conflict - Cannot demote last manager"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Project Members"],
    )
    def patch(self, request, project_id):
        """Handle update member role request."""
        logger.info(
            "Update member role request from user: %s, project_id: %s",
            request.user.email,
            project_id,
        )

        # Validate request data
        serializer = ProjectMemberUpdateRoleSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Update role validation failed for user %s. Errors: %s",
                request.user.email,
                errors,
            )
            return APIResponse.validation_error(
                message="Validation failed", errors=errors
            )

        # Delegate to service layer
        try:
            project_data = self.project_service.update_member_role(
                user=request.user,
                project_id=project_id,
                member_id=serializer.validated_data["user_id"],
                new_role=serializer.validated_data["role"],
            )

            # Serialize response
            response_serializer = ProjectDetailSerializer(project_data)

            logger.info(
                "Member role updated successfully. Project: %s, By: %s",
                project_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Member role updated successfully",
                data=response_serializer.data,
            )

        except ProjectNotFound as e:
            logger.warning("Project not found. ID: %s", project_id)
            return APIResponse.not_found(message=str(e))

        except ProjectMemberNotFound as e:
            logger.warning("Member not found in project %s.", project_id)
            return


# views/project_views.py (add this class)


class ProjectMemberUpdateTagsView(ProjectServiceMixin, APIView):
    """
    Update member tags endpoint.

    PATCH /api/v1/projects/{project_id}/members/tags/

    Request Body:
        {
            "user_id": "uuid",
            "tags": ["frontend", "lead", "reviewer"]
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="projects_update_member_tags",
        summary="Update Member Tags",
        description="Update tags for a project member. Tags replace existing tags entirely. Empty list clears all tags.",
        request=ProjectMemberUpdateTagsSerializer,
        responses={
            200: ProjectDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Project or member not found"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Project Members"],
    )
    def patch(self, request, project_id):
        """Handle update member tags request."""
        logger.info(
            "Update member tags request from user: %s, project_id: %s",
            request.user.email,
            project_id,
        )

        # Validate request data
        serializer = ProjectMemberUpdateTagsSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Update tags validation failed for user %s. Errors: %s",
                request.user.email,
                errors,
            )
            return APIResponse.validation_error(
                message="Validation failed", errors=errors
            )

        # Delegate to service layer
        try:
            project_data = self.project_service.update_member_tags(
                user=request.user,
                project_id=project_id,
                member_id=serializer.validated_data["user_id"],
                tags=serializer.validated_data["tags"],
            )

            # Serialize response
            response_serializer = ProjectDetailSerializer(project_data)

            logger.info(
                "Member tags updated successfully. Project: %s, By: %s",
                project_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Member tags updated successfully",
                data=response_serializer.data,
            )

        except ProjectNotFound as e:
            logger.warning("Project not found. ID: %s", project_id)
            return APIResponse.not_found(message=str(e))

        except ProjectMemberNotFound as e:
            logger.warning("Member not found in project %s.", project_id)
            return APIResponse.not_found(message=str(e))

        except ProjectPermissionDenied as e:
            logger.warning(
                "Permission denied for user %s to update tags in project %s",
                request.user.email,
                project_id,
            )
            return APIResponse.forbidden(message=str(e))

        except Exception as e:
            logger.error(
                "Unexpected error during update tags for project %s. Error: %s",
                project_id,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while updating the member tags"
            )

    def _format_serializer_errors(self, errors):
        """Format serializer errors to a flat dictionary."""
        formatted = {}
        for field, messages in errors.items():
            if isinstance(messages, list):
                formatted[field] = messages[0] if messages else "Invalid value"
            else:
                formatted[field] = str(messages)
        return formatted
