from rest_framework import serializers

from projects.models import ProjectMemberRole, ProjectStatus


class ProjectCreateSerializer(serializers.Serializer):
    """
    Serializer for project creation input validation.

    Validates:
    - title: Required, non-empty, max 200 chars
    - description: Optional, allows blank/null
    - status: Optional, must be valid project status (default: planning)
    - start_date: Optional, valid date format
    - due_date: Optional, valid date format, must be after start_date
    - progress: Optional, 0-100 integer (default: 0)

    Note: Workspace membership and title uniqueness are validated in service layer.
    """

    title = serializers.CharField(
        max_length=200,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            "required": "Project title is required.",
            "blank": "Project title cannot be blank.",
            "max_length": "Project title cannot exceed 200 characters.",
        },
    )

    description = serializers.CharField(
        max_length=5000,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True,
        error_messages={
            "max_length": "Description cannot exceed 5000 characters.",
        },
    )

    status = serializers.ChoiceField(
        choices=ProjectStatus.choices,
        required=False,
        default=ProjectStatus.PLANNING,
        error_messages={
            "invalid_choice": "Invalid project status. Must be one of: planning, in_progress, on_hold, completed, cancelled.",
        },
    )

    start_date = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Start date must be a valid date format (YYYY-MM-DD).",
        },
    )

    due_date = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Due date must be a valid date format (YYYY-MM-DD).",
        },
    )

    progress = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        max_value=100,
        error_messages={
            "invalid": "Progress must be a valid integer.",
            "min_value": "Progress cannot be less than 0%.",
            "max_value": "Progress cannot exceed 100%.",
        },
    )

    def validate_title(self, value):
        """Validate that title is not whitespace-only after trimming."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Project title cannot be empty or whitespace-only."
            )
        return value.strip()

    def validate_description(self, value):
        """Clean description by stripping whitespace if provided."""
        if value:
            return value.strip()
        return value

    def validate(self, data):
        """
        Cross-field validation:
        - due_date must be after start_date if both provided
        - progress must be 0 for planning status
        - progress must be 100 for completed status
        """
        start_date = data.get("start_date")
        due_date = data.get("due_date")
        status = data.get("status", ProjectStatus.PLANNING)
        progress = data.get("progress", 0)

        # Validate date order
        if start_date and due_date and due_date < start_date:
            raise serializers.ValidationError(
                {"due_date": "Due date cannot be before start date."}
            )

        # Validate progress matches status
        if status == ProjectStatus.PLANNING and progress > 0:
            raise serializers.ValidationError(
                {"progress": "Progress must be 0% for projects in planning status."}
            )

        if status == ProjectStatus.COMPLETED and progress < 100:
            raise serializers.ValidationError(
                {"progress": "Progress must be 100% for completed projects."}
            )

        return data


class ProjectUpdateSerializer(serializers.Serializer):
    """
    Serializer for project update input validation.

    All fields are optional for partial updates.
    At least one field must be provided.

    Validates:
    - title: Optional, non-empty, max 200 chars
    - description: Optional, allows blank/null
    - status: Optional, must be valid project status
    - start_date: Optional, valid date format
    - due_date: Optional, valid date format
    - progress: Optional, 0-100 integer
    - is_archived: Optional, boolean

    Note: Workspace membership, permissions, and status transitions
    are validated in service layer.
    """

    title = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            "blank": "Project title cannot be blank.",
            "max_length": "Project title cannot exceed 200 characters.",
        },
    )

    description = serializers.CharField(
        max_length=5000,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True,
        error_messages={
            "max_length": "Description cannot exceed 5000 characters.",
        },
    )

    status = serializers.ChoiceField(
        choices=ProjectStatus.choices,
        required=False,
        error_messages={
            "invalid_choice": "Invalid project status. Must be one of: planning, in_progress, on_hold, completed, cancelled.",
        },
    )

    start_date = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Start date must be a valid date format (YYYY-MM-DD).",
        },
    )

    due_date = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "Due date must be a valid date format (YYYY-MM-DD).",
        },
    )

    progress = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        error_messages={
            "invalid": "Progress must be a valid integer.",
            "min_value": "Progress cannot be less than 0%.",
            "max_value": "Progress cannot exceed 100%.",
        },
    )

    is_archived = serializers.BooleanField(
        required=False,
        error_messages={
            "invalid": "is_archived must be a boolean value.",
        },
    )

    def validate_title(self, value):
        """Validate title if provided, ensure not whitespace-only."""
        if value is not None:
            if not value.strip():
                raise serializers.ValidationError(
                    "Project title cannot be empty or whitespace-only."
                )
            return value.strip()
        return value

    def validate_description(self, value):
        """Clean description if provided."""
        if value is not None and value:
            return value.strip()
        return value

    def validate(self, data):
        """Ensure at least one field is provided for update."""
        if not data:
            raise serializers.ValidationError(
                "At least one field must be provided for update."
            )
        return data


class ProjectListSerializer(serializers.Serializer):
    """
    Serializer for project list response formatting.

    Receives pre-formatted dicts from service layer.
    No database queries executed here.

    Fields:
    - id: Project UUID as string
    - title: Project display name
    - description: Project description (empty string if null)
    - status: Current lifecycle status
    - progress: Completion percentage (0-100)
    - start_date: Start date in ISO format or null
    - due_date: Due date in ISO format or null
    - is_archived: Whether project is archived
    - is_overdue: Whether project is past due date
    - is_active: Whether project is active
    - completion_summary: Human-readable status string
    - days_remaining: Days until due date or null
    - created_by: Dict with creator details (id, email, name)
    - workspace: Dict with workspace details (id, name)
    - user_role: Current user's role in project
    - member_count: Total number of project members
    - created_at: ISO format timestamp
    - updated_at: ISO format timestamp
    """

    id = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_blank=True)
    status = serializers.CharField(read_only=True)
    progress = serializers.IntegerField(read_only=True)
    start_date = serializers.CharField(read_only=True, allow_null=True)
    due_date = serializers.CharField(read_only=True, allow_null=True)
    is_archived = serializers.BooleanField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    completion_summary = serializers.CharField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True, allow_null=True)
    created_by = serializers.DictField(read_only=True)
    workspace = serializers.DictField(read_only=True)
    user_role = serializers.CharField(read_only=True, allow_null=True)
    member_count = serializers.IntegerField(read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)


class ProjectDetailSerializer(serializers.Serializer):
    """
    Serializer for project detail response formatting.

    Receives pre-formatted dicts from service layer.
    No database queries executed here.

    Fields:
    - id: Project UUID as string
    - title: Project display name
    - description: Project description (empty string if null)
    - status: Current lifecycle status
    - progress: Completion percentage (0-100)
    - start_date: Start date in ISO format or null
    - due_date: Due date in ISO format or null
    - is_archived: Whether project is archived
    - is_overdue: Whether project is past due date
    - is_active: Whether project is active
    - completion_summary: Human-readable status string
    - duration_days: Days between start and due date or null
    - days_remaining: Days until due date or null
    - status_color: Hex color for UI display
    - created_by: Dict with creator details (id, email, name)
    - workspace: Dict with workspace details (id, name)
    - user_role: Current user's role in project
    - member_count: Total number of project members
    - members: List of member dicts (id, email, name, role, tags, joined_at)
    - created_at: ISO format timestamp
    - updated_at: ISO format timestamp
    """

    id = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_blank=True)
    status = serializers.CharField(read_only=True)
    progress = serializers.IntegerField(read_only=True)
    start_date = serializers.CharField(read_only=True, allow_null=True)
    due_date = serializers.CharField(read_only=True, allow_null=True)
    is_archived = serializers.BooleanField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    completion_summary = serializers.CharField(read_only=True)
    duration_days = serializers.IntegerField(read_only=True, allow_null=True)
    days_remaining = serializers.IntegerField(read_only=True, allow_null=True)
    status_color = serializers.CharField(read_only=True)
    created_by = serializers.DictField(read_only=True)
    workspace = serializers.DictField(read_only=True)
    user_role = serializers.CharField(read_only=True, allow_null=True)
    member_count = serializers.IntegerField(read_only=True)
    members = serializers.ListField(read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)


class ProjectListQuerySerializer(serializers.Serializer):
    """
    Query parameter serializer for project list endpoint.

    Supports:
    - status: Filter by project status
    - is_archived: Filter by archive status
    - search: Search by title or description
    - sort_by: Sort field (created_at, due_date, title, progress)
    - sort_order: Sort direction (asc, desc)
    """

    status = serializers.ChoiceField(
        choices=ProjectStatus.choices,
        required=False,
        error_messages={
            "invalid_choice": "Invalid project status.",
        },
    )

    is_archived = serializers.BooleanField(
        required=False,
        allow_null=True,
        default=None,
        error_messages={
            "invalid": "is_archived must be a boolean value.",
        },
    )

    search = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
        error_messages={
            "max_length": "Search query cannot exceed 200 characters.",
        },
    )

    sort_by = serializers.ChoiceField(
        choices=["created_at", "due_date", "title", "progress"],
        required=False,
        default="created_at",
        error_messages={
            "invalid_choice": "Sort by must be one of: created_at, due_date, title, progress.",
        },
    )

    sort_order = serializers.ChoiceField(
        choices=["asc", "desc"],
        required=False,
        default="desc",
        error_messages={
            "invalid_choice": "Sort order must be 'asc' or 'desc'.",
        },
    )

    def validate_search(self, value):
        """Clean search query by stripping whitespace."""
        if value:
            return value.strip()
        return value


class ProjectMemberAddSerializer(serializers.Serializer):
    """
    Serializer for adding member to project input validation.

    Validates:
    - user_id: Required, valid UUID format
    - role: Optional, one of 'manager', 'contributor', 'viewer'
    - tags: Optional, list of strings

    Note: Membership existence and permissions are validated in service layer.
    """

    user_id = serializers.UUIDField(
        required=True,
        error_messages={
            "required": "User ID is required.",
            "invalid": "Invalid user ID format. Must be a valid UUID.",
        },
    )

    role = serializers.ChoiceField(
        choices=ProjectMemberRole.choices,
        required=False,
        default=ProjectMemberRole.CONTRIBUTOR,
        error_messages={
            "invalid_choice": "Invalid role. Must be one of: manager, contributor, viewer.",
        },
    )

    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        allow_empty=True,
        error_messages={
            "invalid": "Tags must be a list of strings.",
        },
    )

    def validate_tags(self, value):
        """Remove duplicates and empty strings from tags."""
        if value:
            return list(set(tag.strip() for tag in value if tag.strip()))
        return value


class ProjectMemberRemoveSerializer(serializers.Serializer):
    """
    Serializer for removing member from project input validation.

    Validates:
    - user_id: Required, valid UUID format

    Note: Cannot remove the last manager. Enforced in service layer.
    """

    user_id = serializers.UUIDField(
        required=True,
        error_messages={
            "required": "User ID is required.",
            "invalid": "Invalid user ID format. Must be a valid UUID.",
        },
    )


class ProjectMemberUpdateRoleSerializer(serializers.Serializer):
    """
    Serializer for updating member role input validation.

    Validates:
    - user_id: Required, valid UUID format
    - role: Required, one of 'manager', 'contributor', 'viewer'

    Note: Only project managers or workspace admins can update roles.
    Enforced in service layer.
    """

    user_id = serializers.UUIDField(
        required=True,
        error_messages={
            "required": "User ID is required.",
            "invalid": "Invalid user ID format. Must be a valid UUID.",
        },
    )

    role = serializers.ChoiceField(
        choices=ProjectMemberRole.choices,
        required=True,
        error_messages={
            "required": "Role is required.",
            "invalid_choice": "Invalid role. Must be one of: manager, contributor, viewer.",
        },
    )


class ProjectMemberUpdateTagsSerializer(serializers.Serializer):
    """
    Serializer for updating member tags input validation.

    Validates:
    - user_id: Required, valid UUID format
    - tags: Required, list of strings

    Note: Tags replace existing tags entirely. Use add/remove tag
    endpoints for partial updates.
    """

    user_id = serializers.UUIDField(
        required=True,
        error_messages={
            "required": "User ID is required.",
            "invalid": "Invalid user ID format. Must be a valid UUID.",
        },
    )

    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        allow_empty=True,
        error_messages={
            "required": "Tags list is required.",
            "invalid": "Tags must be a list of strings.",
        },
    )

    def validate_tags(self, value):
        """Remove duplicates and empty strings from tags."""
        if value:
            return list(set(tag.strip() for tag in value if tag.strip()))
        return value


class ProjectStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating project status input validation.

    Validates:
    - status: Required, must be valid project status

    Note: Status transition rules are enforced in service layer.
    Auto-updates progress for completed/cancelled/planning status.
    """

    status = serializers.ChoiceField(
        choices=ProjectStatus.choices,
        required=True,
        error_messages={
            "required": "Status is required.",
            "invalid_choice": "Invalid project status. Must be one of: planning, in_progress, on_hold, completed, cancelled.",
        },
    )


class ProjectProgressUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating project progress input validation.

    Validates:
    - progress: Required, 0-100 integer

    Note: Progress cannot exceed 100% or be negative.
    Progress is auto-set for certain statuses in service layer.
    """

    progress = serializers.IntegerField(
        required=True,
        min_value=0,
        max_value=100,
        error_messages={
            "required": "Progress is required.",
            "invalid": "Progress must be a valid integer.",
            "min_value": "Progress cannot be less than 0%.",
            "max_value": "Progress cannot exceed 100%.",
        },
    )


class ProjectArchiveSerializer(serializers.Serializer):
    """
    Serializer for archiving/unarchiving project input validation.

    Validates:
    - is_archived: Required, boolean

    Note: Only project managers or workspace admins can archive/unarchive.
    Enforced in service layer.
    """

    is_archived = serializers.BooleanField(
        required=True,
        error_messages={
            "required": "is_archived is required.",
            "invalid": "is_archived must be a boolean value.",
        },
    )
