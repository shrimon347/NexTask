import re

from rest_framework import serializers


class WorkspaceCreateSerializer(serializers.Serializer):
    """
    Serializer for workspace creation input validation.

    Validates:
    - name: Required, non-empty, 2-120 characters
    - description: Optional, allows blank/null, max 1000 chars
    - color: Optional, valid hex color code (e.g., #FF5733)

    Note: Workspace name uniqueness per user is not enforced.
    Owner membership creation is handled in service layer.
    """

    name = serializers.CharField(
        max_length=120,
        min_length=2,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            "required": "Workspace name is required.",
            "blank": "Workspace name cannot be blank.",
            "max_length": "Workspace name cannot exceed 120 characters.",
            "min_length": "Workspace name must be at least 2 characters long.",
        },
    )

    description = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True,
        error_messages={
            "max_length": "Description cannot exceed 1000 characters.",
        },
    )

    color = serializers.CharField(
        max_length=7,
        required=False,
        allow_blank=False,
        error_messages={
            "max_length": "Color code cannot exceed 7 characters.",
            "blank": "Color code cannot be blank.",
        },
    )

    def validate_name(self, value):
        """Validate that name is not whitespace-only after trimming."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Workspace name cannot be empty or whitespace-only."
            )
        return value.strip()

    def validate_description(self, value):
        """Clean description by stripping whitespace if provided."""
        if value:
            return value.strip()
        return value

    def validate_color(self, value):
        """Validate color if provided is a valid hex color code.

        Args:
            value: Color string to validate

        Returns:
            str: Uppercase hex color code

        Raises:
            ValidationError: If color format is invalid
        """
        if value is None:
            return value

        # Remove any whitespace
        value = value.strip()

        # Check hex color pattern
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise serializers.ValidationError(
                "Color must be a valid hex color code (e.g., #FF5733)."
            )

        # Normalize to uppercase for consistency
        return value.upper()


class WorkspaceUpdateSerializer(serializers.Serializer):
    """
    Serializer for workspace update input validation.

    All fields are optional - only provided fields will be updated.
    At least one field must be present in the request.

    Validates:
    - name: Optional, non-empty, 2-120 characters
    - description: Optional, allows blank/null, max 1000 chars
    - color: Optional, valid hex color code (e.g., #FF5733)

    Note: Workspace ownership is verified in service layer.
    """

    name = serializers.CharField(
        max_length=120,
        min_length=2,
        required=False,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            "blank": "Workspace name cannot be blank.",
            "max_length": "Workspace name cannot exceed 120 characters.",
            "min_length": "Workspace name must be at least 2 characters long.",
        },
    )

    description = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True,
        error_messages={
            "max_length": "Description cannot exceed 1000 characters.",
        },
    )

    color = serializers.CharField(
        max_length=7,
        required=False,
        allow_blank=False,
        error_messages={
            "max_length": "Color code cannot exceed 7 characters.",
            "blank": "Color code cannot be blank.",
        },
    )

    def validate_name(self, value):
        """Validate name if provided, ensure not whitespace-only."""
        if value is not None:
            if not value.strip():
                raise serializers.ValidationError(
                    "Workspace name cannot be empty or whitespace-only."
                )
            return value.strip()
        return value

    def validate_description(self, value):
        """Clean description if provided."""
        if value is not None and value:
            return value.strip()
        return value

    def validate_color(self, value):
        """Validate color if provided is a valid hex color code.

        Args:
            value: Color string to validate

        Returns:
            str: Uppercase hex color code

        Raises:
            ValidationError: If color format is invalid
        """
        if value is None:
            return value

        # Remove any whitespace
        value = value.strip()

        # Check hex color pattern
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise serializers.ValidationError(
                "Color must be a valid hex color code (e.g., #FF5733)."
            )

        # Normalize to uppercase for consistency
        return value.upper()

    def validate(self, data):
        """Ensure at least one field is provided for update."""
        if not data:
            raise serializers.ValidationError(
                "At least one field must be provided for update."
            )
        return data


class WorkspaceListSerializer(serializers.Serializer):
    """
    Serializer for workspace list response formatting.

    Receives pre-formatted dicts from service layer.
    No database queries executed here.

    Fields:
    - id: Workspace UUID as string
    - name: Workspace display name
    - description: Workspace description (empty string if null)
    - color: Hex color code
    - owner_id: Owner's user UUID
    - owner_email: Owner's email address
    - owner_name: Owner's display name
    - role: Current user's role in workspace
    - member_count: Total number of workspace members
    - created_at: ISO format timestamp
    - updated_at: ISO format timestamp
    """

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_blank=True)
    color = serializers.CharField(read_only=True)
    owner_id = serializers.CharField(read_only=True)
    owner_email = serializers.EmailField(read_only=True)
    owner_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)


class WorkspaceDetailSerializer(serializers.Serializer):
    """
    Serializer for workspace detail response formatting.

    Receives pre-formatted dicts from service layer.
    No database queries executed here.

    Fields:
    - id: Workspace UUID as string
    - name: Workspace display name
    - description: Workspace description (empty string if null)
    - color: Hex color code
    - owner: Dict with owner details (id, email, name)
    - role: Current user's role in workspace
    - member_count: Total number of workspace members
    - project_count: Number of projects in workspace
    - members: List of member dicts (id, email, name, role, joined_at)
    - created_at: ISO format timestamp
    - updated_at: ISO format timestamp
    """

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_blank=True)
    color = serializers.CharField(read_only=True)
    owner = serializers.DictField(read_only=True)
    role = serializers.CharField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    project_count = serializers.IntegerField(read_only=True)
    members = serializers.ListField(read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)


class WorkspaceMemberAddSerializer(serializers.Serializer):
    """
    Serializer for adding member to workspace input validation.

    Validates:
    - user_id: Required, valid UUID format
    - role: Optional, one of 'admin', 'member', 'viewer'

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
        choices=["admin", "member", "viewer"],
        required=False,
        default="member",
        error_messages={
            "invalid_choice": "Invalid role. Must be one of: admin, member, viewer.",
        },
    )


class WorkspaceMemberRemoveSerializer(serializers.Serializer):
    """
    Serializer for removing member from workspace input validation.

    Validates:
    - user_id: Required, valid UUID format

    Note: Cannot remove workspace owner. Enforced in service layer.
    """

    user_id = serializers.UUIDField(
        required=True,
        error_messages={
            "required": "User ID is required.",
            "invalid": "Invalid user ID format. Must be a valid UUID.",
        },
    )


class WorkspaceMemberUpdateRoleSerializer(serializers.Serializer):
    """
    Serializer for updating member role input validation.

    Validates:
    - user_id: Required, valid UUID format
    - role: Required, one of 'admin', 'member', 'viewer'

    Note: Only workspace owner can update roles. Enforced in service layer.
    Cannot change owner's role. Owner role requires ownership transfer.
    """

    user_id = serializers.UUIDField(
        required=True,
        error_messages={
            "required": "User ID is required.",
            "invalid": "Invalid user ID format. Must be a valid UUID.",
        },
    )

    role = serializers.ChoiceField(
        choices=["admin", "member", "viewer"],
        required=True,
        error_messages={
            "required": "Role is required.",
            "invalid_choice": "Invalid role. Must be one of: admin, member, viewer.",
        },
    )


class WorkspaceOwnershipTransferSerializer(serializers.Serializer):
    """
    Serializer for ownership transfer input validation.

    Validates:
    - new_owner_id: Required, valid UUID format

    Note: New owner must be an existing workspace member.
    Only current owner can transfer ownership.
    Both conditions enforced in service layer.
    """

    new_owner_id = serializers.UUIDField(
        required=True,
        error_messages={
            "required": "New owner ID is required.",
            "invalid": "Invalid user ID format. Must be a valid UUID.",
        },
    )
