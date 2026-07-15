from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from core.models import BaseModel

User = get_user_model()


class WorkspaceRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class Workspace(BaseModel):
    """Workspace model for organizing projects and team collaboration.

    A workspace acts as a container for multiple projects and manages
    team members with different access levels (owner, admin, member, viewer).

    Attributes:
        name: Display name for the workspace (max 120 chars)
        description: Optional detailed description
        color: Hex color code for UI representation (default: #FF5733)
        owner: User who created and owns the workspace (PROTECTED from deletion)
        created_at: Timestamp of creation (inherited from BaseModel)
        updated_at: Timestamp of last modification (inherited from BaseModel)
    """

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=16, default="#FF5733")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_workspaces",
    )

    projects = models.ManyToManyField(
        "projects.Project",
        related_name="linked_workspaces",
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["name"]),
        ]
        verbose_name = "Workspace"
        verbose_name_plural = "Workspaces"

    def __str__(self):
        return self.name

    # =========================================================================
    # Convenience Properties & Methods for Member Management
    # =========================================================================

    @property
    def members(self):
        """Get all users who are members of this workspace.

        Returns:
            QuerySet: User objects that are workspace members
        """
        return User.objects.filter(workspace_memberships__workspace=self)

    @property
    def member_count(self):
        """Get total number of members in workspace.

        Uses the prefetch cache when `workspace_memberships` has been
        prefetched (avoids an extra query in list views); falls back to
        a direct COUNT query for single-object access.

        Returns:
            int: Count of workspace members
        """
        if (
            hasattr(self, "_prefetched_objects_cache")
            and "workspace_memberships" in self._prefetched_objects_cache
        ):
            return len(self.workspace_memberships.all())
        return self.workspace_memberships.count()

    @property
    def admin_count(self):
        """Get count of admin members.

        Returns:
            int: Count of admin members
        """
        return self.workspace_memberships.filter(role=WorkspaceRole.ADMIN).count()

    def get_members_with_roles(self):
        """Get all members with their roles and user details (optimized).

        Use this when you need role information, not just user objects.

        Returns:
            QuerySet: WorkspaceMember objects with prefetched user data
        """
        return self.workspace_memberships.select_related("user").all()

    def get_members_by_role(self, role):
        """Get members filtered by specific role.

        Args:
            role: WorkspaceRole enum value

        Returns:
            QuerySet: WorkspaceMember objects for the specified role
        """
        return self.workspace_memberships.filter(role=role).select_related("user")

    def add_member(self, user, role=WorkspaceRole.MEMBER):
        """Add a new member to workspace with specified role.

        Args:
            user: User instance to add as member
            role: Role to assign (default: MEMBER)

        Returns:
            WorkspaceMember: Created membership instance

        Raises:
            ValidationError: If user is already a member
        """
        if self.is_member(user):
            raise ValidationError(
                f"User {user.email} is already a member of this workspace."
            )

        return WorkspaceMember.objects.create(workspace=self, user=user, role=role)

    def remove_member(self, user):
        """Remove a member from workspace.

        Args:
            user: User instance to remove

        Raises:
            ValidationError: If trying to remove the workspace owner
        """
        if self.owner == user:
            raise ValidationError(
                "Cannot remove the workspace owner. "
                "Transfer ownership first or delete the workspace."
            )

        deleted_count, _ = self.workspace_memberships.filter(user=user).delete()
        return deleted_count > 0

    def update_member_role(self, user, new_role):
        """Update a member's role in workspace.

        Args:
            user: User whose role to update
            new_role: New role from WorkspaceRole choices

        Returns:
            WorkspaceMember: Updated membership

        Raises:
            ValidationError: If user is not a member or is the owner
        """
        if not self.is_member(user):
            raise ValidationError(
                f"User {user.email} is not a member of this workspace."
            )

        if self.owner == user:
            raise ValidationError("Cannot change the workspace owner's role.")

        membership = self.workspace_memberships.get(user=user)
        membership.role = new_role
        membership.save(update_fields=["role"])
        return membership

    def is_member(self, user):
        """Check if user is a member of this workspace.

        Args:
            user: User instance to check

        Returns:
            bool: True if user is a member
        """
        return self.workspace_memberships.filter(user=user).exists()

    def get_user_role(self, user):
        """Get the role of a specific user in this workspace.

        Args:
            user: User instance to check role for

        Returns:
            str or None: Role name if member, None otherwise
        """
        try:
            membership = self.workspace_memberships.get(user=user)
            return membership.role
        except WorkspaceMember.DoesNotExist:
            return None

    def is_admin_or_owner(self, user):
        """Check if user has admin or owner privileges.

        Args:
            user: User instance to check

        Returns:
            bool: True if user is admin or owner
        """
        return self.workspace_memberships.filter(
            user=user, role__in=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
        ).exists()

    def has_minimum_role(self, user, min_role):
        """Check if user has at least the specified role level.

        Role hierarchy: owner(4) > admin(3) > member(2) > viewer(1)

        Args:
            user: User instance to check
            min_role: Minimum role required (WorkspaceRole value)

        Returns:
            bool: True if user has sufficient role level
        """
        ROLE_HIERARCHY = {
            WorkspaceRole.OWNER: 4,
            WorkspaceRole.ADMIN: 3,
            WorkspaceRole.MEMBER: 2,
            WorkspaceRole.VIEWER: 1,
        }

        user_role = self.get_user_role(user)
        if not user_role:
            return False

        return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(min_role, 0)


class WorkspaceMember(BaseModel):
    """Membership entity representing a user's membership in a workspace.

    This is a first-class entity that stores the relationship between
    users and workspaces along with role and join date information.

    Attributes:
        workspace: The workspace this membership belongs to
        user: The user who is a member
        role: Access level (owner/admin/member/viewer)
        joined_at: When the user joined (auto-set on creation)
    """

    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="workspace_memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )
    role = models.CharField(
        max_length=32,
        choices=WorkspaceRole.choices,
        default=WorkspaceRole.MEMBER,
        db_index=True,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workspace_members"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "user"], name="uniq_workspace_member"
            ),
        ]
        indexes = [
            models.Index(fields=["workspace", "role"]),
            models.Index(fields=["user", "role"]),
            models.Index(fields=["-joined_at"]),
        ]
        ordering = ["joined_at"]
        verbose_name = "Workspace Member"
        verbose_name_plural = "Workspace Members"

    def __str__(self):
        return f"{self.user.email} - {self.workspace.name} ({self.role})"

    @property
    def is_owner(self):
        """Check if this membership is for owner role."""
        return self.role == WorkspaceRole.OWNER

    @property
    def is_admin(self):
        """Check if this membership is for admin role."""
        return self.role == WorkspaceRole.ADMIN

    @property
    def is_admin_or_owner(self):
        """Check if this membership has elevated privileges."""
        return self.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]

    @property
    def can_manage_members(self):
        """Check if this role can manage workspace members."""
        return self.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]

    @property
    def can_manage_settings(self):
        """Check if this role can modify workspace settings."""
        return self.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
