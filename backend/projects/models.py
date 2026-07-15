# models/project.py

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import BaseModel


class ProjectStatus(models.TextChoices):
    """
    Project lifecycle status choices.

    Represents the current state of a project in its lifecycle:
        PLANNING     - Initial phase, project is being scoped and planned
        IN_PROGRESS  - Active development/work is underway
        ON_HOLD      - Temporarily paused or blocked
        COMPLETED    - Successfully finished all deliverables
        CANCELLED    - Terminated before completion
    """

    PLANNING = "planning", "Planning"
    IN_PROGRESS = "in_progress", "In Progress"
    ON_HOLD = "on_hold", "On Hold"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class ProjectMemberRole(models.TextChoices):
    """
    Project-level member role choices.

    Defines access levels for project members:
        MANAGER     - Full control over project settings, tasks, and members
        CONTRIBUTOR - Can create and modify tasks, upload files
        VIEWER      - Read-only access to project details and tasks
    """

    MANAGER = "manager", "Manager"
    CONTRIBUTOR = "contributor", "Contributor"
    VIEWER = "viewer", "Viewer"


class Project(BaseModel):
    """
    Project model for organizing work within a workspace.

    Projects belong to workspaces and contain tasks, milestones, files,
    and other resources. They inherit workspace membership for basic access
    control but have their own member roles for project-specific permissions.

    Fields:
        - id: UUID primary key
        - title: Project display name (max 200 chars)
        - description: Optional detailed project description
        - workspace: Parent workspace (CASCADE delete)
        - status: Current lifecycle status (default: planning)
        - start_date: Optional project start date
        - due_date: Optional project deadline
        - progress: Completion percentage 0-100 (default: 0)
        - created_by: User who created the project (PROTECT delete)
        - is_archived: Soft delete flag (default: False)
        - created_at: Creation timestamp
        - updated_at: Update timestamp

    Notes:
        - member_count and user_role are derived via annotations in service layer
        - progress auto-updates are handled in service layer
        - All listed properties use ONLY model fields, no DB queries
    """

    title = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Project display name (required, max 200 characters)",
    )

    description = models.TextField(
        blank=True, default="", help_text="Optional detailed project description"
    )

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="workspace_projects",
        db_index=True,
        help_text="Parent workspace this project belongs to",
    )

    status = models.CharField(
        max_length=32,
        choices=ProjectStatus.choices,
        default=ProjectStatus.PLANNING,
        db_index=True,
        help_text="Current project lifecycle status",
    )

    start_date = models.DateField(
        blank=True, null=True, help_text="Optional project start date"
    )

    due_date = models.DateField(
        blank=True, null=True, db_index=True, help_text="Optional project deadline"
    )

    progress = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0, message="Progress cannot be less than 0%"),
            MaxValueValidator(100, message="Progress cannot exceed 100%"),
        ],
        help_text="Project completion percentage (0-100)",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_projects",
        db_index=True,
        help_text="User who created this project",
    )

    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Soft delete flag - archived projects are hidden by default",
    )

    class Meta:
        db_table = "project"
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        indexes = [
            models.Index(fields=["workspace", "status"], name="project_ws_status_idx"),
            models.Index(
                fields=["workspace", "-created_at"], name="project_ws_created_idx"
            ),
            models.Index(
                fields=["workspace", "is_archived"], name="project_ws_archived_idx"
            ),
            models.Index(
                fields=["created_by", "-created_at"], name="project_creator_created_idx"
            ),
            models.Index(fields=["status", "due_date"], name="project_status_due_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""),
                name="chk_project_title_not_empty",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.workspace.name})"

    # =========================================================================
    # LIGHTWEIGHT PROPERTIES - NO DB QUERIES, Model Fields Only
    # =========================================================================

    @property
    def is_overdue(self):
        """
        Check if project is past its due date and not completed/cancelled.

        Uses only: self.due_date, self.status, timezone.now()

        Returns:
            bool: True if overdue, False if no due_date or completed/cancelled
        """
        if not self.due_date:
            return False
        if self.status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]:
            return False
        return timezone.now().date() > self.due_date

    @property
    def is_active(self):
        """
        Check if project is currently active (not archived/completed/cancelled).

        Uses only: self.is_archived, self.status

        Returns:
            bool: True if project is active and workable
        """
        return not self.is_archived and self.status not in [
            ProjectStatus.COMPLETED,
            ProjectStatus.CANCELLED,
        ]

    @property
    def completion_summary(self):
        """
        Get human-readable completion status string.

        Uses only: self.status, self.progress, self.is_overdue

        Returns:
            str: Summary like "75% complete" or "Completed" or "Overdue"
        """
        if self.status == ProjectStatus.COMPLETED:
            return "Completed"
        if self.status == ProjectStatus.CANCELLED:
            return "Cancelled"
        if self.status == ProjectStatus.ON_HOLD:
            return f"On Hold - {self.progress}%"
        if self.is_overdue:
            return f"Overdue - {self.progress}%"
        if self.status == ProjectStatus.PLANNING:
            return "Planning"
        return f"{self.progress}% complete"

    @property
    def duration_days(self):
        """
        Calculate duration between start_date and due_date in days.

        Uses only: self.start_date, self.due_date

        Returns:
            int or None: Number of days, or None if either date is missing
        """
        if self.start_date and self.due_date:
            return (self.due_date - self.start_date).days
        return None

    @property
    def days_remaining(self):
        """
        Calculate days remaining until due_date from today.

        Uses only: self.due_date, timezone.now()

        Returns:
            int or None: Days remaining (negative if overdue), None if no due_date
        """
        if not self.due_date:
            return None
        return (self.due_date - timezone.now().date()).days

    @property
    def is_completed_late(self):
        """
        Check if project was completed after its due date.

        Uses only: self.status, self.due_date
        NO DB QUERY - safe to use anywhere.

        Returns:
            bool: True if completed but past due date
        """
        if self.status == ProjectStatus.COMPLETED and self.due_date:
            # Note: This is approximate since we don't have completed_at timestamp
            # For precise check, add completed_at field to the model
            return False  # Can't determine without completed_at
        return False

    @property
    def status_color(self):
        """
        Get color code based on project status for UI display.

        Uses only: self.status, self.is_overdue
        NO DB QUERY - safe for UI rendering.

        Returns:
            str: Hex color code for the status
        """
        if self.status == ProjectStatus.COMPLETED:
            return "#10B981"  # Green
        if self.status == ProjectStatus.CANCELLED:
            return "#EF4444"  # Red
        if self.is_overdue:
            return "#F59E0B"  # Amber/Yellow
        if self.status == ProjectStatus.ON_HOLD:
            return "#6B7280"  # Gray
        if self.status == ProjectStatus.IN_PROGRESS:
            return "#3B82F6"  # Blue
        return "#8B5CF6"  # Purple for Planning


class ProjectMember(BaseModel):
    """
    Membership entity representing a user's membership in a project.

    This is a first-class entity that stores the relationship between
    users and projects along with role and metadata information.

    Fields:
        - id: UUID primary key
        - user: The user who is a project member (CASCADE delete)
        - project: The project this membership belongs to (CASCADE delete)
        - role: Access level from ProjectMemberRole choices (default: contributor)
        - tags: Flexible JSON array for member categorization
        - created_at: When member was added
        - updated_at: Last modification timestamp

    Notes:
        - Unique constraint on (user, project) prevents duplicate memberships
        - Tags are flexible metadata (e.g., ['frontend', 'lead', 'reviewer'])
        - All listed properties use ONLY model fields, no DB queries
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
        db_index=True,
        help_text="User who is a project member",
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="project_memberships",
        db_index=True,
        help_text="Project this membership belongs to",
    )

    role = models.CharField(
        max_length=32,
        choices=ProjectMemberRole.choices,
        default=ProjectMemberRole.CONTRIBUTOR,
        db_index=True,
        help_text="Member's access level in this project",
    )

    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Flexible tags for member categorization (e.g., ['frontend', 'lead'])",
    )

    class Meta:
        db_table = "project_member"
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "project"], name="uniq_project_member"
            ),
        ]
        indexes = [
            models.Index(fields=["project", "role"], name="pm_project_role_idx"),
            models.Index(fields=["user", "role"], name="pm_user_role_idx"),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.project.title} ({self.role})"

    # =========================================================================
    # LIGHTWEIGHT PROPERTIES - NO DB QUERIES, Model Fields Only
    # =========================================================================

    @property
    def is_manager(self):
        """
        Check if this membership has manager role.

        Uses only: self.role
        NO DB QUERY - safe to use in loops and permission checks.

        Returns:
            bool: True if role is manager
        """
        return self.role == ProjectMemberRole.MANAGER

    @property
    def is_contributor(self):
        """
        Check if this membership has contributor role.

        Uses only: self.role
        NO DB QUERY - safe to use in loops and permission checks.

        Returns:
            bool: True if role is contributor
        """
        return self.role == ProjectMemberRole.CONTRIBUTOR

    @property
    def is_viewer(self):
        """
        Check if this membership has viewer role.

        Uses only: self.role
        NO DB QUERY - safe to use in loops and permission checks.

        Returns:
            bool: True if role is viewer
        """
        return self.role == ProjectMemberRole.VIEWER

    @property
    def can_edit(self):
        """
        Check if this member can modify project content.

        Manager and contributor roles can edit.
        Uses only: self.role
        NO DB QUERY - safe for permission checks.

        Returns:
            bool: True if member can edit project content
        """
        return self.role in [ProjectMemberRole.MANAGER, ProjectMemberRole.CONTRIBUTOR]

    @property
    def can_manage_members(self):
        """
        Check if this member can manage project members.

        Only manager role can manage members.
        Uses only: self.role
        NO DB QUERY - safe for permission checks.

        Returns:
            bool: True if member can manage other members
        """
        return self.role == ProjectMemberRole.MANAGER

    @property
    def tag_count(self):
        """
        Get number of tags assigned to this member.

        Uses only: self.tags
        NO DB QUERY - safe for display purposes.

        Returns:
            int: Number of tags
        """
        return len(self.tags) if self.tags else 0

    @property
    def tags_display(self):
        """
        Get comma-separated string of tags for display.

        Uses only: self.tags
        NO DB QUERY - safe for display purposes.

        Returns:
            str: Comma-separated tags or empty string
        """
        return ", ".join(self.tags) if self.tags else ""
