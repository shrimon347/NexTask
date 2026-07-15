import logging

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.exceptions import ValidationError
from core.responses import APIResponse

from .exceptions import (
    WorkspaceMemberNotFound,
    WorkspaceNotFound,
    WorkspacePermissionDenied,
)
from .mixins import WorkspaceServiceMixin
from .serializers import (
    WorkspaceCreateSerializer,
    WorkspaceDetailSerializer,
    WorkspaceListSerializer,
    WorkspaceMemberAddSerializer,
    WorkspaceMemberRemoveSerializer,
    WorkspaceMemberUpdateRoleSerializer,
    WorkspaceOwnershipTransferSerializer,
    WorkspaceUpdateSerializer,
)

logger = logging.getLogger(__name__)


class WorkspaceListCreateView(WorkspaceServiceMixin, APIView):
    """
    Workspace list and create endpoint.

    GET /api/v1/workspaces/
    POST /api/v1/workspaces/

    GET Query Parameters:
        - search: Search term for workspace name/description (optional)

    POST Request Body:
        {
            "name": "My Workspace",
            "description": "Optional description",
            "color": "#FF5733"
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="workspaces_list",
        summary="List Workspaces",
        description="List all workspaces where the authenticated user is a member. Results include user's role and member count.",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search workspaces by name or description",
                required=False,
                type=str,
            ),
        ],
        responses={
            200: WorkspaceListSerializer(many=True),
            400: OpenApiResponse(description="Invalid query parameters"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
        },
        tags=["Workspaces"],
    )
    def get(self, request):
        """
        Handle workspace list request.

        Returns flat list of workspaces with user's role and member count.
        """
        logger.info(
            "Workspace list request from user: %s, search: %s",
            request.user.email,
            request.query_params.get("search", None),
        )

        # Extract query parameters
        search_query = request.query_params.get("search", None)

        # Delegate to service layer
        try:
            workspaces = self.workspace_service.list_user_workspaces(
                user=request.user,
                search_query=search_query,
            )

            # Serialize response
            response_serializer = WorkspaceListSerializer(workspaces, many=True)

            logger.info(
                "Workspaces retrieved successfully for user %s. Count: %d",
                request.user.email,
                len(workspaces),
            )

            return APIResponse.success(
                message="Workspaces retrieved successfully",
                data=response_serializer.data,
            )

        except Exception as e:
            logger.error(
                "Unexpected error during workspace list for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while retrieving workspaces"
            )

    @extend_schema(
        operation_id="workspaces_create",
        summary="Create Workspace",
        description="Create a new workspace. The authenticated user automatically becomes the workspace owner.",
        request=WorkspaceCreateSerializer,
        responses={
            201: WorkspaceDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Workspaces"],
    )
    def post(self, request):
        """Handle workspace creation request."""
        logger.info(
            "Workspace creation request from user: %s",
            request.user.email,
        )

        # Validate request data
        serializer = WorkspaceCreateSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Workspace creation validation failed for user %s. Errors: %s",
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
            workspace_data = self.workspace_service.create_workspace(
                user=request.user,
                name=validated_data["name"],
                description=validated_data.get("description", ""),
                color=validated_data.get("color", "#FF5733"),
            )

            # Serialize response
            response_serializer = WorkspaceDetailSerializer(workspace_data)

            logger.info(
                "Workspace created successfully. ID: %s, User: %s",
                workspace_data.get("id"),
                request.user.email,
            )

            return APIResponse.created(
                message="Workspace created successfully",
                data=response_serializer.data,
            )

        except ValidationError as e:
            logger.warning(
                "Workspace creation failed for user %s. Error: %s",
                request.user.email,
                str(e),
            )
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during workspace creation for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while creating the workspace"
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


class WorkspaceDetailView(WorkspaceServiceMixin, APIView):
    """
    Workspace detail, update, and delete endpoint.

    GET /api/v1/workspaces/{workspace_id}/
    PATCH /api/v1/workspaces/{workspace_id}/
    DELETE /api/v1/workspaces/{workspace_id}/
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="workspaces_retrieve",
        summary="Get Workspace Details",
        description="Retrieve detailed workspace information including all members with their roles.",
        responses={
            200: WorkspaceDetailSerializer,
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Not a workspace member"),
            404: OpenApiResponse(description="Workspace not found"),
        },
        tags=["Workspaces"],
    )
    def get(self, request, workspace_id):
        """Handle workspace detail retrieval request."""
        logger.info(
            "Workspace detail request from user: %s, workspace_id: %s",
            request.user.email,
            workspace_id,
        )

        try:
            workspace_data = self.workspace_service.get_workspace_details(
                user=request.user,
                workspace_id=workspace_id,
            )

            # Serialize response
            response_serializer = WorkspaceDetailSerializer(workspace_data)

            logger.info(
                "Workspace details retrieved successfully. ID: %s, User: %s",
                workspace_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Workspace details retrieved successfully",
                data=response_serializer.data,
            )

        except WorkspaceNotFound as e:
            logger.warning(
                "Workspace not found for user %s. ID: %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.not_found(message=str(e))

        except WorkspacePermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on workspace %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.forbidden(message=str(e))

        except Exception as e:
            logger.error(
                "Unexpected error during workspace retrieval for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while retrieving the workspace"
            )

    @extend_schema(
        operation_id="workspaces_update",
        summary="Update Workspace",
        description="Update workspace settings. Only the workspace owner can update settings. At least one field must be provided.",
        request=WorkspaceUpdateSerializer,
        responses={
            200: WorkspaceDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Not the workspace owner"),
            404: OpenApiResponse(description="Workspace not found"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Workspaces"],
    )
    def patch(self, request, workspace_id):
        """Handle workspace update request."""
        logger.info(
            "Workspace update request from user: %s, workspace_id: %s",
            request.user.email,
            workspace_id,
        )

        # Validate request data
        serializer = WorkspaceUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Workspace update validation failed for user %s. Errors: %s",
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
            workspace_data = self.workspace_service.update_workspace(
                user=request.user,
                workspace_id=workspace_id,
                **validated_data,
            )

            # Serialize response
            response_serializer = WorkspaceDetailSerializer(workspace_data)

            logger.info(
                "Workspace updated successfully. ID: %s, User: %s",
                workspace_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Workspace updated successfully",
                data=response_serializer.data,
            )

        except WorkspaceNotFound as e:
            logger.warning(
                "Workspace not found for user %s. ID: %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.not_found(message=str(e))

        except WorkspacePermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on workspace %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning(
                "Workspace update failed for user %s. Error: %s",
                request.user.email,
                str(e),
            )
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during workspace update for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while updating the workspace"
            )

    @extend_schema(
        operation_id="workspaces_delete",
        summary="Delete Workspace",
        description="Delete a workspace and all associated data. Only the workspace owner can delete. This action is irreversible.",
        responses={
            200: OpenApiResponse(description="Workspace deleted successfully"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Not the workspace owner"),
            404: OpenApiResponse(description="Workspace not found"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Workspaces"],
    )
    def delete(self, request, workspace_id):
        """Handle workspace deletion request."""
        logger.info(
            "Workspace deletion request from user: %s, workspace_id: %s",
            request.user.email,
            workspace_id,
        )

        try:
            self.workspace_service.delete_workspace(
                user=request.user,
                workspace_id=workspace_id,
            )

            logger.info(
                "Workspace deleted successfully. ID: %s, User: %s",
                workspace_id,
                request.user.email,
            )

            return APIResponse.success(
                message="Workspace deleted successfully",
                data=None,
            )

        except WorkspaceNotFound as e:
            logger.warning(
                "Workspace not found for user %s. ID: %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.not_found(message=str(e))

        except WorkspacePermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on workspace %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.forbidden(message=str(e))

        except Exception as e:
            logger.error(
                "Unexpected error during workspace deletion for user %s. Error: %s",
                request.user.email,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while deleting the workspace"
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


class WorkspaceMemberAddView(WorkspaceServiceMixin, APIView):
    """
    Add member to workspace endpoint.

    POST /api/v1/workspaces/{workspace_id}/members/add/

    Request Body:
        {
            "user_id": "uuid",
            "role": "member"
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="workspaces_add_member",
        summary="Add Workspace Member",
        description="Add a new member to workspace. Only admins and owners can add members.",
        request=WorkspaceMemberAddSerializer,
        responses={
            200: WorkspaceDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Workspace or user not found"),
            409: OpenApiResponse(description="Conflict - User already a member"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Workspace Members"],
    )
    def post(self, request, workspace_id):
        """Handle add member request."""
        logger.info(
            "Add member request from user: %s, workspace_id: %s",
            request.user.email,
            workspace_id,
        )

        # Validate request data
        serializer = WorkspaceMemberAddSerializer(data=request.data)

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

        # Extract validated data
        validated_data = serializer.validated_data

        # Delegate to service layer
        try:
            workspace_data = self.workspace_service.add_member(
                user=request.user,
                workspace_id=workspace_id,
                member_id=str(validated_data["user_id"]),
                role=validated_data.get("role", "member"),
            )

            # Serialize response
            response_serializer = WorkspaceDetailSerializer(workspace_data)

            logger.info(
                "Member added successfully. Workspace: %s, Member: %s, By: %s",
                workspace_id,
                validated_data["user_id"],
                request.user.email,
            )

            return APIResponse.success(
                message="Member added successfully",
                data=response_serializer.data,
            )

        except WorkspaceNotFound as e:
            logger.warning("Workspace not found. ID: %s", workspace_id)
            return APIResponse.not_found(message=str(e))

        except WorkspaceMemberNotFound as e:
            logger.warning(
                "User not found for member addition. User: %s",
                validated_data["user_id"],
            )
            return APIResponse.not_found(message=str(e))

        except WorkspacePermissionDenied as e:
            logger.warning(
                "Permission denied for user %s to add member to workspace %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning("Add member failed. Error: %s", str(e))
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during add member for workspace %s. Error: %s",
                workspace_id,
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


class WorkspaceMemberRemoveView(WorkspaceServiceMixin, APIView):
    """
    Remove member from workspace endpoint.

    POST /api/v1/workspaces/{workspace_id}/members/remove/

    Request Body:
        {
            "user_id": "uuid"
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="workspaces_remove_member",
        summary="Remove Workspace Member",
        description="Remove a member from workspace. Admins/owners can remove others. Members can remove themselves (leave workspace).",
        request=WorkspaceMemberRemoveSerializer,
        responses={
            200: WorkspaceDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Insufficient permissions"),
            404: OpenApiResponse(description="Workspace or member not found"),
            409: OpenApiResponse(description="Conflict - Cannot remove owner"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Workspace Members"],
    )
    def post(self, request, workspace_id):
        """Handle remove member request."""
        logger.info(
            "Remove member request from user: %s, workspace_id: %s",
            request.user.email,
            workspace_id,
        )

        # Validate request data
        serializer = WorkspaceMemberRemoveSerializer(data=request.data)

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

        # Extract validated data
        validated_data = serializer.validated_data

        # Delegate to service layer
        try:
            workspace_data = self.workspace_service.remove_member(
                user=request.user,
                workspace_id=workspace_id,
                member_id=str(validated_data["user_id"]),
            )

            # Serialize response
            response_serializer = WorkspaceDetailSerializer(workspace_data)

            logger.info(
                "Member removed successfully. Workspace: %s, Member: %s, By: %s",
                workspace_id,
                validated_data["user_id"],
                request.user.email,
            )

            return APIResponse.success(
                message="Member removed successfully",
                data=response_serializer.data,
            )

        except WorkspaceNotFound as e:
            logger.warning("Workspace not found. ID: %s", workspace_id)
            return APIResponse.not_found(message=str(e))

        except WorkspaceMemberNotFound as e:
            logger.warning(
                "Member not found in workspace %s. User: %s",
                workspace_id,
                validated_data["user_id"],
            )
            return APIResponse.not_found(message=str(e))

        except WorkspacePermissionDenied as e:
            logger.warning(
                "Permission denied for user %s to remove member from workspace %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning("Remove member failed. Error: %s", str(e))
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during remove member for workspace %s. Error: %s",
                workspace_id,
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


class WorkspaceMemberUpdateRoleView(WorkspaceServiceMixin, APIView):
    """
    Update member role endpoint.

    POST /api/v1/workspaces/{workspace_id}/members/update-role/

    Request Body:
        {
            "user_id": "uuid",
            "role": "admin"
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="workspaces_update_member_role",
        summary="Update Member Role",
        description="Update a member's role in workspace. Only the workspace owner can change roles.",
        request=WorkspaceMemberUpdateRoleSerializer,
        responses={
            200: WorkspaceDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Not the workspace owner"),
            404: OpenApiResponse(description="Workspace or member not found"),
            409: OpenApiResponse(description="Conflict - Cannot change owner's role"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Workspace Members"],
    )
    def post(self, request, workspace_id):
        """Handle update member role request."""
        logger.info(
            "Update member role request from user: %s, workspace_id: %s",
            request.user.email,
            workspace_id,
        )

        # Validate request data
        serializer = WorkspaceMemberUpdateRoleSerializer(data=request.data)

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

        # Extract validated data
        validated_data = serializer.validated_data

        # Delegate to service layer
        try:
            workspace_data = self.workspace_service.update_member_role(
                user=request.user,
                workspace_id=workspace_id,
                member_id=str(validated_data["user_id"]),
                new_role=validated_data["role"],
            )

            # Serialize response
            response_serializer = WorkspaceDetailSerializer(workspace_data)

            logger.info(
                "Member role updated successfully. Workspace: %s, Member: %s, New Role: %s",
                workspace_id,
                validated_data["user_id"],
                validated_data["role"],
            )

            return APIResponse.success(
                message="Member role updated successfully",
                data=response_serializer.data,
            )

        except WorkspaceNotFound as e:
            logger.warning("Workspace not found. ID: %s", workspace_id)
            return APIResponse.not_found(message=str(e))

        except WorkspaceMemberNotFound as e:
            logger.warning(
                "Member not found in workspace %s. User: %s",
                workspace_id,
                validated_data["user_id"],
            )
            return APIResponse.not_found(message=str(e))

        except WorkspacePermissionDenied as e:
            logger.warning(
                "Permission denied for user %s to update role in workspace %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning("Update role failed. Error: %s", str(e))
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during update role for workspace %s. Error: %s",
                workspace_id,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while updating the member role"
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


class WorkspaceTransferOwnershipView(WorkspaceServiceMixin, APIView):
    """
    Transfer workspace ownership endpoint.

    POST /api/v1/workspaces/{workspace_id}/transfer-ownership/

    Request Body:
        {
            "new_owner_id": "uuid"
        }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="workspaces_transfer_ownership",
        summary="Transfer Workspace Ownership",
        description="Transfer workspace ownership to another member. Only the current owner can transfer. New owner must be an existing member.",
        request=WorkspaceOwnershipTransferSerializer,
        responses={
            200: WorkspaceDetailSerializer,
            400: OpenApiResponse(description="Validation error - invalid request data"),
            401: OpenApiResponse(description="Unauthorized - Authentication required"),
            403: OpenApiResponse(description="Forbidden - Not the workspace owner"),
            404: OpenApiResponse(description="Workspace or new owner not found"),
            409: OpenApiResponse(description="Conflict - New owner not a member"),
            500: OpenApiResponse(description="Internal server error"),
        },
        tags=["Workspaces"],
    )
    def post(self, request, workspace_id):
        """Handle ownership transfer request."""
        logger.info(
            "Ownership transfer request from user: %s, workspace_id: %s",
            request.user.email,
            workspace_id,
        )

        # Validate request data
        serializer = WorkspaceOwnershipTransferSerializer(data=request.data)

        if not serializer.is_valid():
            errors = self._format_serializer_errors(serializer.errors)
            logger.warning(
                "Ownership transfer validation failed for user %s. Errors: %s",
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
            workspace_data = self.workspace_service.transfer_ownership(
                user=request.user,
                workspace_id=workspace_id,
                new_owner_id=str(validated_data["new_owner_id"]),
            )

            # Serialize response
            response_serializer = WorkspaceDetailSerializer(workspace_data)

            logger.info(
                "Ownership transferred successfully. Workspace: %s, New Owner: %s",
                workspace_id,
                validated_data["new_owner_id"],
            )

            return APIResponse.success(
                message="Workspace ownership transferred successfully",
                data=response_serializer.data,
            )

        except WorkspaceNotFound as e:
            logger.warning("Workspace not found. ID: %s", workspace_id)
            return APIResponse.not_found(message=str(e))

        except WorkspaceMemberNotFound as e:
            logger.warning(
                "New owner not found. User: %s", validated_data["new_owner_id"]
            )
            return APIResponse.not_found(message=str(e))

        except WorkspacePermissionDenied as e:
            logger.warning(
                "Permission denied for user %s to transfer ownership of workspace %s",
                request.user.email,
                workspace_id,
            )
            return APIResponse.forbidden(message=str(e))

        except ValidationError as e:
            logger.warning("Ownership transfer failed. Error: %s", str(e))
            return APIResponse.conflict(
                message=str(e.message) if hasattr(e, "message") else str(e)
            )

        except Exception as e:
            logger.error(
                "Unexpected error during ownership transfer for workspace %s. Error: %s",
                workspace_id,
                str(e),
                exc_info=True,
            )
            return APIResponse.server_error(
                message="An error occurred while transferring ownership"
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
