import logging
from typing import Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, OuterRef, Prefetch, Q, Subquery

from workspaces.exceptions import (
    WorkspaceMemberNotFound,
    WorkspaceNotFound,
    WorkspacePermissionDenied,
)

from .models import Workspace, WorkspaceMember, WorkspaceRole

logger = logging.getLogger(__name__)


class WorkspaceService:
    """
    Service class for workspace business logic.

    Responsibilities:
    - Create workspaces with owner membership
    - Enforce role-based access control
    - Manage workspace members (add, remove, update roles)
    - Handle workspace ownership transfer
    - List workspaces with optimized queries
    - Provide workspace details with member information
    """

    def __init__(self):
        self.logger = logger

    # =========================================================================
    # WORKSPACE CREATION & RETRIEVAL
    # =========================================================================

    @transaction.atomic
    def create_workspace(
        self, user, name: str, description: str = "", color: str = "#FF5733"
    ) -> Dict:
        """
        Create a new workspace with owner membership.

        Business Rules:
        - Workspace name is trimmed before storage
        - Creator automatically becomes owner member
        - All operations are atomic

        Args:
            user: User instance (request.user)
            name: Workspace name
            description: Optional workspace description
            color: Hex color code (default: '#FF5733')

        Returns:
            Dict: Workspace detail payload

        Raises:
            ValidationError: If workspace creation fails
        """
        # Normalize inputs
        normalized_name = name.strip()
        normalized_description = description.strip() if description else ""

        self.logger.info(
            "Creating workspace for user %s: name=%s, color=%s",
            user.email,
            normalized_name,
            color,
        )

        # Create workspace
        workspace = Workspace.objects.create(
            name=normalized_name,
            description=normalized_description,
            color=color,
            owner=user,
        )

        # Add creator as owner member
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=user,
            role=WorkspaceRole.OWNER,
        )

        self.logger.info(
            "Workspace created successfully. ID: %s, User: %s, Name: %s",
            workspace.id,
            user.email,
            normalized_name,
        )

        # Return full details
        return self.get_workspace_details(user=user, workspace_id=str(workspace.id))

    def list_user_workspaces(
        self, user, search_query: Optional[str] = None
    ) -> List[Dict]:
        """
        List all workspaces where user is a member.

        Uses optimized single query with subqueries to avoid N+1 problems.
        Returns plain dicts - no ORM objects exposed to callers.

        Business Rules:
        - Only returns workspaces where user is a member
        - Annotates user's role and total member count
        - Ordered by most recently created first

        Args:
            user: User instance (request.user)
            search_query: Optional search term for workspace name

        Returns:
            List[Dict]: List of workspace payloads with keys:
                id, name, description, color,
                owner_id, owner_email, owner_name,
                role, member_count, created_at, updated_at
        """
        self.logger.info(
            "Listing workspaces for user %s, search: %s",
            user.email,
            search_query,
        )

        # Subquery to get user's role in each workspace
        user_role_subquery = WorkspaceMember.objects.filter(
            workspace=OuterRef("pk"),
            user=user,
        ).values("role")[:1]

        # Build optimized query
        queryset = (
            Workspace.objects.filter(workspace_memberships__user=user)
            .select_related("owner")
            .annotate(
                user_role=Subquery(user_role_subquery),
                total_members=Count("workspace_memberships", distinct=True),
            )
            .distinct()
        )

        # Apply search filter
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )

        # Order by most recent first
        workspaces = queryset.order_by("-created_at")

        # Convert to dicts - ALL data is now in memory
        workspace_list = []
        for workspace in workspaces:
            workspace_list.append(
                {
                    "id": str(workspace.id),
                    "name": workspace.name,
                    "description": workspace.description or "",
                    "color": workspace.color,
                    "owner_id": str(workspace.owner.id),
                    "owner_email": workspace.owner.email,
                    "owner_name": workspace.owner.name,
                    "role": workspace.user_role,
                    "member_count": workspace.total_members,
                    "created_at": workspace.created_at.isoformat(),
                    "updated_at": workspace.updated_at.isoformat(),
                }
            )

        self.logger.info(
            "Workspaces retrieved for user %s. Count: %d",
            user.email,
            len(workspace_list),
        )

        return workspace_list

    def get_workspace_details(self, user, workspace_id: str) -> Dict:
        """
        Get workspace details with full member information.

        Uses optimized queries with select_related and prefetch_related
        to fetch all data in minimal database hits.

        Business Rules:
        - User must be a workspace member to access details
        - Returns all member information with roles

        Args:
            user: User instance (request.user)
            workspace_id: Workspace UUID as string

        Returns:
            Dict: Workspace detail payload with keys:
                id, name, description, color,
                owner, role, member_count, project_count,
                members, created_at, updated_at

        Raises:
            WorkspaceNotFound: If workspace doesn't exist
            WorkspacePermissionDenied: If user is not a member
        """
        self.logger.info(
            "Getting workspace details. ID: %s, User: %s",
            workspace_id,
            user.email,
        )

        # Single optimized query with all related data
        try:
            workspace = (
                Workspace.objects.select_related("owner")
                .prefetch_related(
                    Prefetch(
                        "workspace_memberships",
                        queryset=WorkspaceMember.objects.select_related(
                            "user"
                        ).order_by("joined_at"),
                    )
                )
                .get(id=workspace_id)
            )
        except Workspace.DoesNotExist:
            self.logger.warning(
                "Workspace not found. ID: %s, User: %s",
                workspace_id,
                user.email,
            )
            raise WorkspaceNotFound(f"Workspace with id {workspace_id} not found")

        # Process members and find current user's membership
        user_membership = None
        members_list = []

        for membership in workspace.workspace_memberships.all():
            member_data = {
                "id": str(membership.user.id),
                "email": membership.user.email,
                "name": membership.user.name,
                "profile_picture": getattr(membership.user, "avatar", None),
                "role": membership.role,
                "joined_at": membership.joined_at.isoformat(),
            }
            members_list.append(member_data)

            # Track current user's membership
            if membership.user_id == user.id:
                user_membership = membership

        # Verify user is a member
        if not user_membership:
            self.logger.warning(
                "User %s is not a member of workspace %s",
                user.email,
                workspace_id,
            )
            raise WorkspacePermissionDenied("You are not a member of this workspace.")

        # Build complete payload
        detail = {
            "id": str(workspace.id),
            "name": workspace.name,
            "description": workspace.description or "",
            "color": workspace.color,
            "owner": {
                "id": str(workspace.owner.id),
                "email": workspace.owner.email,
                "name": workspace.owner.name,
            },
            "role": user_membership.role,
            "member_count": len(members_list),
            "project_count": 0,  # Update when Project model exists
            "members": members_list,
            "created_at": workspace.created_at.isoformat(),
            "updated_at": workspace.updated_at.isoformat(),
        }

        self.logger.info(
            "Workspace details retrieved. ID: %s, User: %s, Role: %s, Members: %d",
            workspace_id,
            user.email,
            user_membership.role,
            len(members_list),
        )

        return detail

    # =========================================================================
    # WORKSPACE UPDATE & DELETE
    # =========================================================================

    @transaction.atomic
    def update_workspace(
        self,
        user,
        workspace_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Dict:
        """
        Update workspace fields.

        Business Rules:
        - Only workspace owner can update settings
        - Only provided fields are updated
        - Name is trimmed before storage

        Args:
            user: User instance (request.user)
            workspace_id: Workspace UUID as string
            name: Optional new workspace name
            description: Optional new description
            color: Optional new color

        Returns:
            Dict: Updated workspace detail payload

        Raises:
            WorkspaceNotFound: If workspace doesn't exist
            WorkspacePermissionDenied: If user is not the owner
        """
        self.logger.info(
            "Updating workspace %s by user %s. Fields: name=%s, color=%s",
            workspace_id,
            user.email,
            name,
            color,
        )

        # Get workspace
        workspace = self._get_workspace_by_id(workspace_id)

        # Verify ownership
        if workspace.owner != user:
            self.logger.warning(
                "User %s attempted to update workspace %s without owner permission",
                user.email,
                workspace_id,
            )
            raise WorkspacePermissionDenied(
                "Only the workspace owner can update settings."
            )

        # Update fields
        if name is not None:
            workspace.name = name.strip()
        if description is not None:
            workspace.description = description.strip() if description else ""
        if color is not None:
            workspace.color = color

        workspace.save(
            update_fields=[
                field
                for field in ["name", "description", "color"]
                if locals().get(field) is not None
            ]
        )

        self.logger.info(
            "Workspace updated successfully. ID: %s, User: %s",
            workspace_id,
            user.email,
        )

        # Return updated details
        return self.get_workspace_details(user=user, workspace_id=workspace_id)

    @transaction.atomic
    def delete_workspace(self, user, workspace_id: str) -> None:
        """
        Delete a workspace and all associated data.

        Business Rules:
        - Only workspace owner can delete
        - Cascading delete removes all members, projects, etc.

        Args:
            user: User instance (request.user)
            workspace_id: Workspace UUID as string

        Raises:
            WorkspaceNotFound: If workspace doesn't exist
            WorkspacePermissionDenied: If user is not the owner
        """
        self.logger.info(
            "Deleting workspace %s by user %s",
            workspace_id,
            user.email,
        )

        # Get workspace
        workspace = self._get_workspace_by_id(workspace_id)

        # Verify ownership
        if workspace.owner != user:
            self.logger.warning(
                "User %s attempted to delete workspace %s without owner permission",
                user.email,
                workspace_id,
            )
            raise WorkspacePermissionDenied(
                "Only the workspace owner can delete the workspace."
            )

        workspace_name = workspace.name
        workspace.delete()

        self.logger.info(
            "Workspace deleted successfully. ID: %s, Name: %s, User: %s",
            workspace_id,
            workspace_name,
            user.email,
        )

    # =========================================================================
    # MEMBER MANAGEMENT
    # =========================================================================

    @transaction.atomic
    def add_member(
        self, user, workspace_id: str, member_id: str, role: str = "member"
    ) -> Dict:
        """
        Add a member to workspace.

        Business Rules:
        - Only admins and owners can add members
        - User cannot be added if already a member
        - Role defaults to 'member'

        Args:
            user: User instance (request.user) - performing the action
            workspace_id: Workspace UUID as string
            member_id: User UUID to add as member
            role: Role to assign (admin/member/viewer)

        Returns:
            Dict: Updated workspace detail payload

        Raises:
            WorkspaceNotFound: If workspace doesn't exist
            WorkspacePermissionDenied: If user lacks permission
            ValidationError: If user is already a member
        """
        self.logger.info(
            "Adding member to workspace %s. Member: %s, Role: %s, By: %s",
            workspace_id,
            member_id,
            role,
            user.email,
        )

        # Get workspace
        workspace = self._get_workspace_by_id(workspace_id)

        # Verify permission
        if not self._is_admin_or_owner(workspace, user):
            self.logger.warning(
                "User %s attempted to add member without admin permission. Workspace: %s",
                user.email,
                workspace_id,
            )
            raise WorkspacePermissionDenied("Only admins and owners can add members.")

        # Get member user
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            member_user = User.objects.get(id=member_id)
        except User.DoesNotExist:
            self.logger.warning("User not found. Member ID: %s", member_id)
            raise WorkspaceMemberNotFound(f"User with id {member_id} not found")

        # Check if already a member
        if workspace.is_member(member_user):
            self.logger.warning(
                "User %s is already a member of workspace %s",
                member_user.email,
                workspace_id,
            )
            raise ValidationError(
                f"User {member_user.email} is already a member of this workspace."
            )

        # Create membership
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=member_user,
            role=role,
        )

        self.logger.info(
            "Member added successfully. Workspace: %s, Member: %s, Role: %s",
            workspace_id,
            member_user.email,
            role,
        )

        # Return updated details
        return self.get_workspace_details(user=user, workspace_id=workspace_id)

    @transaction.atomic
    def remove_member(self, user, workspace_id: str, member_id: str) -> Dict:
        """
        Remove a member from workspace.

        Business Rules:
        - Only admins and owners can remove members
        - Cannot remove the workspace owner
        - Users can remove themselves (leave workspace)

        Args:
            user: User instance (request.user) - performing the action
            workspace_id: Workspace UUID as string
            member_id: User UUID to remove

        Returns:
            Dict: Updated workspace detail payload

        Raises:
            WorkspaceNotFound: If workspace doesn't exist
            WorkspacePermissionDenied: If user lacks permission
            ValidationError: If attempting to remove owner
        """
        self.logger.info(
            "Removing member from workspace %s. Member: %s, By: %s",
            workspace_id,
            member_id,
            user.email,
        )

        # Get workspace
        workspace = self._get_workspace_by_id(workspace_id)

        # Get member user
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            member_user = User.objects.get(id=member_id)
        except User.DoesNotExist:
            self.logger.warning("User not found. Member ID: %s", member_id)
            raise WorkspaceMemberNotFound(f"User with id {member_id} not found")

        # Cannot remove owner
        if workspace.owner == member_user:
            self.logger.warning(
                "Attempted to remove workspace owner. Workspace: %s, Owner: %s",
                workspace_id,
                member_user.email,
            )
            raise ValidationError(
                "Cannot remove the workspace owner. "
                "Transfer ownership first or delete the workspace."
            )

        # Permission check (allow self-removal)
        if user != member_user and not self._is_admin_or_owner(workspace, user):
            self.logger.warning(
                "User %s attempted to remove member without permission. Workspace: %s",
                user.email,
                workspace_id,
            )
            raise WorkspacePermissionDenied(
                "Only admins and owners can remove other members."
            )

        # Remove membership
        deleted_count, _ = WorkspaceMember.objects.filter(
            workspace=workspace,
            user=member_user,
        ).delete()

        if deleted_count > 0:
            self.logger.info(
                "Member removed successfully. Workspace: %s, Member: %s",
                workspace_id,
                member_user.email,
            )
        else:
            self.logger.warning(
                "Member not found in workspace. Workspace: %s, Member: %s",
                workspace_id,
                member_user.email,
            )
            raise WorkspaceMemberNotFound(
                f"User {member_user.email} is not a member of this workspace."
            )

        # Return updated details
        return self.get_workspace_details(user=user, workspace_id=workspace_id)

    @transaction.atomic
    def update_member_role(
        self, user, workspace_id: str, member_id: str, new_role: str
    ) -> Dict:
        """
        Update a member's role in workspace.

        Business Rules:
        - Only workspace owner can change roles
        - Cannot change the owner's role
        - Role must be one of: admin, member, viewer

        Args:
            user: User instance (request.user) - must be owner
            workspace_id: Workspace UUID as string
            member_id: User UUID whose role to update
            new_role: New role to assign

        Returns:
            Dict: Updated workspace detail payload

        Raises:
            WorkspaceNotFound: If workspace doesn't exist
            WorkspacePermissionDenied: If user is not the owner
            ValidationError: If attempting to change owner's role
        """
        self.logger.info(
            "Updating member role. Workspace: %s, Member: %s, New Role: %s, By: %s",
            workspace_id,
            member_id,
            new_role,
            user.email,
        )

        # Get workspace
        workspace = self._get_workspace_by_id(workspace_id)

        # Only owner can change roles
        if workspace.owner != user:
            self.logger.warning(
                "User %s attempted to update role without owner permission. Workspace: %s",
                user.email,
                workspace_id,
            )
            raise WorkspacePermissionDenied(
                "Only the workspace owner can change member roles."
            )

        # Get member user
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            member_user = User.objects.get(id=member_id)
        except User.DoesNotExist:
            self.logger.warning("User not found. Member ID: %s", member_id)
            raise WorkspaceMemberNotFound(f"User with id {member_id} not found")

        # Cannot change owner's role
        if workspace.owner == member_user:
            self.logger.warning(
                "Attempted to change owner's role. Workspace: %s, Owner: %s",
                workspace_id,
                member_user.email,
            )
            raise ValidationError(
                "Cannot change the workspace owner's role. "
                "Transfer ownership to change the owner's role."
            )

        # Update role
        try:
            membership = WorkspaceMember.objects.get(
                workspace=workspace,
                user=member_user,
            )
            old_role = membership.role
            membership.role = new_role
            membership.save(update_fields=["role"])
        except WorkspaceMember.DoesNotExist:
            self.logger.warning(
                "Member not found in workspace. Workspace: %s, Member: %s",
                workspace_id,
                member_user.email,
            )
            raise WorkspaceMemberNotFound(
                f"User {member_user.email} is not a member of this workspace."
            )

        self.logger.info(
            "Member role updated. Workspace: %s, Member: %s, Role: %s -> %s",
            workspace_id,
            member_user.email,
            old_role,
            new_role,
        )

        # Return updated details
        return self.get_workspace_details(user=user, workspace_id=workspace_id)

    # =========================================================================
    # OWNERSHIP TRANSFER
    # =========================================================================

    @transaction.atomic
    def transfer_ownership(self, user, workspace_id: str, new_owner_id: str) -> Dict:
        """
        Transfer workspace ownership to another member.

        Business Rules:
        - Only current owner can transfer ownership
        - New owner must be an existing workspace member
        - Old owner becomes admin after transfer
        - New owner's role is updated to owner

        Args:
            user: User instance (request.user) - must be current owner
            workspace_id: Workspace UUID as string
            new_owner_id: User UUID of new owner

        Returns:
            Dict: Updated workspace detail payload

        Raises:
            WorkspaceNotFound: If workspace doesn't exist
            WorkspacePermissionDenied: If user is not the owner
            ValidationError: If new owner is not a member
        """
        self.logger.info(
            "Transferring ownership. Workspace: %s, New Owner: %s, By: %s",
            workspace_id,
            new_owner_id,
            user.email,
        )

        # Get workspace
        workspace = self._get_workspace_by_id(workspace_id)

        # Verify current ownership
        if workspace.owner != user:
            self.logger.warning(
                "User %s attempted to transfer ownership without being owner. Workspace: %s",
                user.email,
                workspace_id,
            )
            raise WorkspacePermissionDenied(
                "Only the current owner can transfer ownership."
            )

        # Get new owner user
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            new_owner = User.objects.get(id=new_owner_id)
        except User.DoesNotExist:
            self.logger.warning("New owner user not found. ID: %s", new_owner_id)
            raise WorkspaceMemberNotFound(f"User with id {new_owner_id} not found")

        # Verify new owner is a member
        if not workspace.is_member(new_owner):
            self.logger.warning(
                "New owner %s is not a workspace member. Workspace: %s",
                new_owner.email,
                workspace_id,
            )
            raise ValidationError("New owner must be an existing workspace member.")

        # Update workspace owner
        old_owner_email = workspace.owner.email
        workspace.owner = new_owner
        workspace.save(update_fields=["owner"])

        # Update membership roles
        WorkspaceMember.objects.filter(
            workspace=workspace,
            user=user,
        ).update(role=WorkspaceRole.ADMIN)

        WorkspaceMember.objects.filter(
            workspace=workspace,
            user=new_owner,
        ).update(role=WorkspaceRole.OWNER)

        self.logger.info(
            "Ownership transferred successfully. Workspace: %s, From: %s, To: %s",
            workspace_id,
            old_owner_email,
            new_owner.email,
        )

        # Return updated details
        return self.get_workspace_details(user=user, workspace_id=workspace_id)

    # =========================================================================
    # PRIVATE HELPER METHODS
    # =========================================================================

    def _get_workspace_by_id(self, workspace_id: str) -> Workspace:
        """
        Get workspace by ID with consistent error handling.

        Args:
            workspace_id: Workspace UUID as string

        Returns:
            Workspace: Workspace instance

        Raises:
            WorkspaceNotFound: If workspace doesn't exist
        """
        try:
            return Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            self.logger.warning("Workspace not found. ID: %s", workspace_id)
            raise WorkspaceNotFound(f"Workspace with id {workspace_id} not found")

    def _is_admin_or_owner(self, workspace: Workspace, user) -> bool:
        """
        Check if user has admin or owner role in workspace.

        Args:
            workspace: Workspace instance
            user: User instance to check

        Returns:
            bool: True if user is admin or owner
        """
        return workspace.workspace_memberships.filter(
            user=user,
            role__in=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN],
        ).exists()

    def _verify_membership(self, workspace: Workspace, user) -> None:
        """
        Verify user is a workspace member, raise if not.

        Args:
            workspace: Workspace instance
            user: User instance to verify

        Raises:
            WorkspacePermissionDenied: If user is not a member
        """
        if not workspace.is_member(user):
            self.logger.warning(
                "User %s is not a member of workspace %s",
                user.email,
                workspace.id,
            )
            raise WorkspacePermissionDenied("You are not a member of this workspace.")
