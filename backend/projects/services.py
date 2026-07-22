# services/project_service.py
import logging
import uuid
from typing import Dict, List, Optional

from django.db import transaction
from django.db.models import Count, OuterRef, Prefetch, Q, Subquery

from core.exceptions import ValidationError
from projects.exceptions import (
    ProjectMemberNotFound,
    ProjectNotFound,
    ProjectPermissionDenied,
)
from workspaces.models import Workspace, WorkspaceRole

from .models import Project, ProjectMember, ProjectMemberRole, ProjectStatus

logger = logging.getLogger(__name__)


class ProjectService:
    """
    Service class for project business logic.

    Responsibilities:
    - Create projects with business rule validation
    - Enforce title uniqueness within workspace
    - Validate workspace membership and permissions
    - Manage project members (add, remove, update roles, update tags)
    - Handle project status transitions with progress auto-updates
    - Archive/unarchive projects (soft delete)
    - List projects with optimized N+1 safe queries
    - Provide project details with member information
    - Bulk member operations with partial success
    """

    def __init__(self):
        self.logger = logger

    # =========================================================================
    # PROJECT CREATION & RETRIEVAL
    # =========================================================================

    @transaction.atomic
    def create_project(
        self,
        user,
        workspace_id: uuid.UUID,
        title: str,
        description: str = "",
        status: str = ProjectStatus.PLANNING,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        progress: int = 0,
        tags: Optional[List[str]] = None,
        members: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Create a new project within a workspace.

        Business Rules:
        - User must be a workspace member with minimum 'member' role
        - Project title must be unique within workspace (case-insensitive)
        - Title is trimmed before validation
        - Creator automatically becomes project manager with tags
        - Additional members added if provided (must be workspace members)
        - Progress auto-set to 0 for planning, 100 for completed status

        Args:
            user: User instance (request.user)
            workspace_id: Workspace UUID
            title: Project title
            description: Optional project description
            status: Project status (default: planning)
            start_date: Optional start date
            due_date: Optional due date
            progress: Completion percentage (default: 0)
            tags: Optional list of tags for creator's membership
            members: Optional list of {"user": uuid, "role": str} dicts

        Returns:
            Dict: Project detail payload

        Raises:
            WorkspaceNotFound: If workspace doesn't exist
            ProjectPermissionDenied: If user is not workspace member
            ValidationError: If project title already exists or validation fails
        """
        # Normalize inputs
        normalized_title = title.strip()
        normalized_description = description.strip() if description else ""

        self.logger.info(
            "Creating project for user %s: title=%s, workspace=%s, status=%s, members=%d",
            user.email,
            normalized_title,
            workspace_id,
            status,
            len(members) if members else 0,
        )

        # Verify workspace exists and user is member
        workspace = self._get_workspace(workspace_id)
        self._verify_workspace_member(workspace, user)

        # Verify user has permission to create projects
        if not workspace.has_minimum_role(user, WorkspaceRole.MEMBER):
            self.logger.warning(
                "User %s lacks permission to create projects in workspace %s",
                user.email,
                workspace_id,
            )
            raise ProjectPermissionDenied(
                "You don't have permission to create projects in this workspace."
            )

        # Validate title uniqueness within workspace
        self._validate_title_uniqueness(workspace, normalized_title)

        # Apply business logic for progress based on status
        if status == ProjectStatus.COMPLETED:
            progress = 100
        elif status == ProjectStatus.PLANNING:
            progress = 0

        # Create project
        project = Project.objects.create(
            workspace=workspace,
            title=normalized_title,
            description=normalized_description,
            status=status,
            start_date=start_date,
            due_date=due_date,
            progress=progress,
            created_by=user,
        )

        # Add creator as manager member with tags
        ProjectMember.objects.create(
            project=project,
            user=user,
            role=ProjectMemberRole.MANAGER,
            tags=tags or [],
        )

        # Add additional members if provided
        added_members = []
        failed_members = []

        if members:
            for member_data in members:
                try:
                    member_user = self._get_user(member_data["user"])

                    # Verify workspace membership
                    if not workspace.is_member(member_user):
                        failed_members.append(
                            {
                                "user": str(member_data["user"]),
                                "error": "User is not a workspace member.",
                            }
                        )
                        continue

                    # Skip if already added (creator)
                    if member_user.id == user.id:
                        continue

                    # Check if already a project member
                    if self._is_project_member(project, member_user):
                        failed_members.append(
                            {
                                "user": str(member_data["user"]),
                                "email": member_user.email,
                                "error": "User is already a member of this project.",
                            }
                        )
                        continue

                    # Create membership
                    ProjectMember.objects.create(
                        project=project,
                        user=member_user,
                        role=member_data.get("role", ProjectMemberRole.CONTRIBUTOR),
                    )
                    added_members.append(str(member_data["user"]))

                except ProjectMemberNotFound:
                    failed_members.append(
                        {
                            "user": str(member_data["user"]),
                            "error": "User not found.",
                        }
                    )

        self.logger.info(
            "Project created successfully. ID: %s, User: %s, Title: %s, Status: %s, Added: %d, Failed: %d",
            project.id,
            user.email,
            normalized_title,
            status,
            len(added_members),
            len(failed_members),
        )

        # Return full details
        return self.get_project_details(user=user, project_id=str(project.id))

    def list_projects(
        self,
        user,
        workspace_id: uuid.UUID,
        status: Optional[str] = None,
        is_archived: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> List[Dict]:
        """
        List projects in a workspace with optimized N+1 safe queries.

        Uses annotations for user_role and member_count to avoid N+1 problems.
        Returns plain dicts - no ORM objects exposed to callers.

        Business Rules:
        - User must be a workspace member to view projects
        - Archived projects hidden by default (unless is_archived=True)
        - Supports filtering by status, search, and sorting

        Args:
            user: User instance (request.user)
            workspace_id: Workspace UUID
            status: Filter by project status (optional)
            is_archived: Filter by archive status (optional, None = show active only)
            search: Search by title or description (optional)
            sort_by: Sort field (created_at, due_date, title, progress)
            sort_order: Sort direction (asc, desc)

        Returns:
            List[Dict]: List of project payloads with keys:
                id, title, description, status, progress,
                start_date, due_date, is_archived,
                is_overdue, is_active, completion_summary, days_remaining,
                created_by, workspace, user_role, member_count,
                created_at, updated_at
        """
        self.logger.info(
            "Listing projects for user %s, workspace: %s, status: %s, is_archived: %s, search: %s",
            user.email,
            workspace_id,
            status,
            is_archived,
            search,
        )

        # Verify workspace exists and user is member
        workspace = self._get_workspace(workspace_id)
        self._verify_workspace_member(workspace, user)

        # Subquery to get user's role in each project
        user_role_subquery = ProjectMember.objects.filter(
            project=OuterRef("pk"),
            user=user,
        ).values("role")[:1]

        # Build optimized query
        queryset = (
            Project.objects.filter(workspace=workspace)
            .select_related("created_by", "workspace")
            .annotate(
                user_role=Subquery(user_role_subquery),
                member_count=Count("project_memberships", distinct=True),
            )
        )

        # Apply filters
        if is_archived is None:
            # Default: show only active projects
            queryset = queryset.filter(is_archived=False)
        elif is_archived is not None:
            queryset = queryset.filter(is_archived=is_archived)

        if status:
            queryset = queryset.filter(status=status)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # Apply sorting
        sort_prefix = "-" if sort_order == "desc" else ""
        sort_mapping = {
            "created_at": f"{sort_prefix}created_at",
            "due_date": f"{sort_prefix}due_date",
            "title": f"{sort_prefix}title",
            "progress": f"{sort_prefix}progress",
        }
        sort_field = sort_mapping.get(sort_by, f"{sort_prefix}created_at")
        queryset = queryset.order_by(sort_field)

        # Convert to dicts - ALL data in memory, NO more queries
        project_list = []
        for project in queryset:
            project_list.append(self._build_list_payload(project))

        self.logger.info(
            "Projects retrieved for user %s. Workspace: %s, Count: %d",
            user.email,
            workspace_id,
            len(project_list),
        )

        return project_list

    def get_project_details(self, user, project_id: str) -> Dict:
        """
        Get project details with full member information.

        Uses optimized queries with select_related and prefetch_related
        to fetch all data in minimal database hits.

        Business Rules:
        - User must be a project member or workspace admin to access details
        - Returns all member information with roles and tags

        Args:
            user: User instance (request.user)
            project_id: Project UUID as string

        Returns:
            Dict: Project detail payload with keys:
                id, title, description, status, progress,
                start_date, due_date, is_archived,
                is_overdue, is_active, completion_summary,
                duration_days, days_remaining, status_color,
                created_by, workspace, user_role, member_count,
                members, created_at, updated_at

        Raises:
            ProjectNotFound: If project doesn't exist
            ProjectPermissionDenied: If user lacks access
        """
        self.logger.info(
            "Getting project details. ID: %s, User: %s",
            project_id,
            user.email,
        )

        # Single optimized query with all related data
        try:
            project = (
                Project.objects.select_related("created_by", "workspace")
                .prefetch_related(
                    Prefetch(
                        "project_memberships",
                        queryset=ProjectMember.objects.select_related("user").order_by(
                            "created_at"
                        ),
                    )
                )
                .get(id=project_id)
            )
        except Project.DoesNotExist:
            self.logger.warning(
                "Project not found. ID: %s, User: %s",
                project_id,
                user.email,
            )
            raise ProjectNotFound(f"Project with id {project_id} not found")

        # Verify user has access (project member or workspace admin)
        user_membership = self._get_user_membership(project, user)
        is_workspace_admin = project.workspace.is_admin_or_owner(user)

        if not user_membership and not is_workspace_admin:
            self.logger.warning(
                "User %s lacks access to project %s",
                user.email,
                project_id,
            )
            raise ProjectPermissionDenied("You don't have access to this project.")

        # Build member list
        members_list = []
        for (
            membership
        ) in project.project_memberships.all():  # Prefetched, NO extra query
            members_list.append(
                {
                    "id": str(membership.user.id),
                    "email": membership.user.email,
                    "name": membership.user.name,
                    "profile_picture": getattr(
                        membership.user, "profile_picture", None
                    ),
                    "role": membership.role,
                    "tags": membership.tags,
                    "joined_at": membership.created_at.isoformat(),
                }
            )

        # Build detail payload
        detail = self._build_detail_payload(
            project=project,
            user_membership=user_membership,
            members_list=members_list,
        )

        self.logger.info(
            "Project details retrieved. ID: %s, User: %s, Role: %s, Members: %d",
            project_id,
            user.email,
            user_membership.role if user_membership else "workspace_admin",
            len(members_list),
        )

        return detail

    # =========================================================================
    # PROJECT UPDATE & DELETE
    # =========================================================================

    @transaction.atomic
    def update_project(self, user, project_id: str, **update_fields) -> Dict:
        """
        Update project fields.

        Business Rules:
        - Only project manager or workspace admin can update
        - Title uniqueness is validated if title is being changed
        - Cannot update archived projects (unarchive first)
        - Progress auto-updates based on status changes
        - tags: None=skip, []=clear, [...] = replace creator's tags
        - members: None=skip, []=clear all, [...] = replace all members

        Args:
            user: User instance (request.user)
            project_id: Project UUID as string
            **update_fields: Fields to update (title, description, status,
                start_date, due_date, progress, is_archived, tags, members)

        Returns:
            Dict: Updated project detail payload

        Raises:
            ProjectNotFound: If project not found
            ProjectPermissionDenied: If user lacks permission
            ValidationError: If title conflict or validation fails
        """
        self.logger.info(
            "Updating project %s by user %s. Fields: %s",
            project_id,
            user.email,
            list(update_fields.keys()),
        )

        # Get project
        project = self._get_project(project_id)

        # Verify permission (project manager or workspace admin)
        self._verify_can_manage(project, user)

        # Cannot update archived projects (unless unarchiving)
        if project.is_archived and not update_fields.get("is_archived"):
            self.logger.warning(
                "Update attempted on archived project. ID: %s, User: %s",
                project_id,
                user.email,
            )
            raise ValidationError(
                "Cannot update an archived project. Unarchive it first."
            )

        # Extract non-model fields
        tags = update_fields.pop("tags", None)
        members = update_fields.pop("members", None)

        # Validate title uniqueness if changing title
        if "title" in update_fields:
            normalized_title = update_fields["title"].strip()
            if normalized_title != project.title:
                self._validate_title_uniqueness(
                    project.workspace, normalized_title, exclude_id=project.id
                )
            update_fields["title"] = normalized_title

        # Handle status transition logic
        if "status" in update_fields:
            new_status = update_fields.pop("status")
            self._apply_status_transition(project, new_status)

        # Apply model field updates
        for field, value in update_fields.items():
            setattr(project, field, value)

        project.save()

        # Handle tags update (creator's membership tags)
        if tags is not None:
            creator_membership = ProjectMember.objects.get(
                project=project,
                user=project.created_by,
            )
            creator_membership.tags = tags
            creator_membership.save(update_fields=["tags", "updated_at"])

        # Handle members update (replace all members)
        if members is not None:
            self._replace_project_members(project, members)

        self.logger.info(
            "Project updated successfully. ID: %s, User: %s",
            project_id,
            user.email,
        )

        # Return updated details
        return self.get_project_details(user=user, project_id=project_id)

    @transaction.atomic
    def delete_project(self, user, project_id: str) -> None:
        """
        Permanently delete a project.

        Business Rules:
        - Only workspace owner or project creator can delete
        - Cascading delete removes all members, tasks, etc.

        Args:
            user: User instance (request.user)
            project_id: Project UUID as string

        Raises:
            ProjectNotFound: If project not found
            ProjectPermissionDenied: If user lacks permission
        """
        self.logger.info(
            "Deleting project %s by user %s",
            project_id,
            user.email,
        )

        # Get project
        project = self._get_project(project_id)

        # Only workspace owner or project creator can delete
        is_workspace_owner = project.workspace.owner == user
        is_project_creator = project.created_by == user

        if not (is_workspace_owner or is_project_creator):
            self.logger.warning(
                "User %s attempted to delete project %s without permission",
                user.email,
                project_id,
            )
            raise ProjectPermissionDenied(
                "Only the workspace owner or project creator can delete the project."
            )

        project_title = project.title
        project.delete()

        self.logger.info(
            "Project deleted successfully. ID: %s, Title: %s, User: %s",
            project_id,
            project_title,
            user.email,
        )

    # =========================================================================
    # PROJECT STATUS & PROGRESS
    # =========================================================================

    @transaction.atomic
    def update_status(self, user, project_id: str, new_status: str) -> Dict:
        """
        Update project status with transition rules.

        Business Rules:
        - Only project manager or workspace admin can update status
        - Auto-set progress: completed=100%, planning=0%
        - Cannot change status of archived projects

        Args:
            user: User instance (request.user)
            project_id: Project UUID as string
            new_status: New status from ProjectStatus choices

        Returns:
            Dict: Updated project detail payload

        Raises:
            ProjectNotFound: If project not found
            ProjectPermissionDenied: If user lacks permission
            ValidationError: If invalid status transition
        """
        self.logger.info(
            "Updating project status. ID: %s, New Status: %s, User: %s",
            project_id,
            new_status,
            user.email,
        )

        # Get project
        project = self._get_project(project_id)

        # Verify permission
        self._verify_can_manage(project, user)

        # Cannot update archived projects
        if project.is_archived:
            raise ValidationError(
                "Cannot change status of an archived project. Unarchive it first."
            )

        # Apply status transition
        old_status = project.status
        self._apply_status_transition(project, new_status)
        project.save()

        self.logger.info(
            "Project status updated. ID: %s, Status: %s -> %s, User: %s",
            project_id,
            old_status,
            new_status,
            user.email,
        )

        # Return updated details
        return self.get_project_details(user=user, project_id=project_id)

    @transaction.atomic
    def update_progress(self, user, project_id: str, progress: int) -> Dict:
        """
        Update project progress manually.

        Business Rules:
        - Only project manager, contributor, or workspace admin can update
        - Progress cannot be set for planning status
        - Progress auto-set to 100 if status is completed

        Args:
            user: User instance (request.user)
            project_id: Project UUID as string
            progress: New progress value (0-100)

        Returns:
            Dict: Updated project detail payload

        Raises:
            ProjectNotFound: If project not found
            ProjectPermissionDenied: If user lacks permission
            ValidationError: If progress update is invalid
        """
        self.logger.info(
            "Updating project progress. ID: %s, Progress: %d%%, User: %s",
            project_id,
            progress,
            user.email,
        )

        # Get project
        project = self._get_project(project_id)

        # Verify permission (manager, contributor, or workspace admin)
        user_membership = self._get_user_membership(project, user)
        is_workspace_admin = project.workspace.is_admin_or_owner(user)

        if not user_membership and not is_workspace_admin:
            raise ProjectPermissionDenied(
                "You don't have permission to update this project's progress."
            )

        if user_membership and user_membership.role == ProjectMemberRole.VIEWER:
            raise ProjectPermissionDenied("Viewers cannot update project progress.")

        # Cannot update archived projects
        if project.is_archived:
            raise ValidationError("Cannot update progress of an archived project.")

        # Cannot set progress for planning status
        if project.status == ProjectStatus.PLANNING:
            raise ValidationError(
                "Cannot set progress for projects in planning status."
            )

        # If completed, force 100%
        if project.status == ProjectStatus.COMPLETED:
            progress = 100

        project.progress = progress
        project.save(update_fields=["progress", "updated_at"])

        self.logger.info(
            "Project progress updated. ID: %s, Progress: %d%%, User: %s",
            project_id,
            progress,
            user.email,
        )

        # Return updated details
        return self.get_project_details(user=user, project_id=project_id)

    # =========================================================================
    # PROJECT ARCHIVE
    # =========================================================================

    @transaction.atomic
    def toggle_archive(self, user, project_id: str, is_archived: bool) -> Dict:
        """
        Archive or unarchive a project.

        Business Rules:
        - Only project manager or workspace admin can archive/unarchive

        Args:
            user: User instance (request.user)
            project_id: Project UUID as string
            is_archived: True to archive, False to unarchive

        Returns:
            Dict: Updated project detail payload

        Raises:
            ProjectNotFound: If project not found
            ProjectPermissionDenied: If user lacks permission
        """
        self.logger.info(
            "%s project %s by user %s",
            "Archiving" if is_archived else "Unarchiving",
            project_id,
            user.email,
        )

        # Get project
        project = self._get_project(project_id)

        # Verify permission
        self._verify_can_manage(project, user)

        project.is_archived = is_archived
        project.save(update_fields=["is_archived", "updated_at"])

        self.logger.info(
            "Project %s successfully. ID: %s, User: %s",
            "archived" if is_archived else "unarchived",
            project_id,
            user.email,
        )

        # Return updated details
        return self.get_project_details(user=user, project_id=project_id)

    # =========================================================================
    # MEMBER MANAGEMENT
    # =========================================================================

    @transaction.atomic
    def add_member(
        self,
        user,
        project_id: str,
        member_id: uuid.UUID,
        role: str = ProjectMemberRole.CONTRIBUTOR,
        tags: Optional[List[str]] = None,
    ) -> Dict:
        """
        Add a member to project.

        Business Rules:
        - Only project manager or workspace admin can add members
        - User must be a workspace member first
        - User cannot be added if already a project member
        - Role defaults to contributor

        Args:
            user: User instance (request.user) - performing the action
            project_id: Project UUID as string
            member_id: User UUID to add as member
            role: Role to assign (default: contributor)
            tags: Optional list of tags

        Returns:
            Dict: Updated project detail payload

        Raises:
            ProjectNotFound: If project not found
            ProjectPermissionDenied: If user lacks permission
            ProjectMemberNotFound: If member user not found
            ValidationError: If user is already a member or not in workspace
        """
        self.logger.info(
            "Adding member to project %s. Member: %s, Role: %s, By: %s",
            project_id,
            member_id,
            role,
            user.email,
        )

        # Get project
        project = self._get_project(project_id)

        # Verify permission
        self._verify_can_manage(project, user)

        # Get member user
        member_user = self._get_user(member_id)

        # Verify member is workspace member
        if not project.workspace.is_member(member_user):
            self.logger.warning(
                "User %s is not a workspace member. Workspace: %s",
                member_user.email,
                project.workspace.id,
            )
            raise ValidationError(
                "User must be a workspace member before adding to project."
            )

        # Check if already a project member
        if self._is_project_member(project, member_user):
            self.logger.warning(
                "User %s is already a member of project %s",
                member_user.email,
                project_id,
            )
            raise ValidationError(
                f"User {member_user.email} is already a member of this project."
            )

        # Create membership
        ProjectMember.objects.create(
            project=project,
            user=member_user,
            role=role,
            tags=tags or [],
        )

        self.logger.info(
            "Member added successfully. Project: %s, Member: %s, Role: %s",
            project_id,
            member_user.email,
            role,
        )

        # Return updated details
        return self.get_project_details(user=user, project_id=project_id)

    @transaction.atomic
    def add_members_bulk(
        self,
        user,
        project_id: str,
        members: List[Dict],
    ) -> Dict:
        """
        Add multiple members to project in bulk.

        Business Rules:
        - Only project manager or workspace admin can add members
        - All users must be workspace members
        - Users already in project are skipped with warning
        - Partial success: successful additions are saved, failures reported

        Args:
            user: User instance (request.user)
            project_id: Project UUID as string
            members: List of {"user": uuid, "role": str} dicts

        Returns:
            Dict: {
                "project": project_detail_dict,
                "added": [user_ids],
                "failed": [{"user": uuid, "error": str}]
            }
        """
        self.logger.info(
            "Bulk adding %d members to project %s by user %s",
            len(members),
            project_id,
            user.email,
        )

        project = self._get_project(project_id)
        self._verify_can_manage(project, user)

        added = []
        failed = []

        for member_data in members:
            try:
                member_user = self._get_user(member_data["user"])
                role = member_data.get("role", ProjectMemberRole.CONTRIBUTOR)

                # Verify workspace membership
                if not project.workspace.is_member(member_user):
                    failed.append(
                        {
                            "user": str(member_data["user"]),
                            "email": member_user.email,
                            "error": "User is not a workspace member.",
                        }
                    )
                    continue

                # Check if already a project member
                if self._is_project_member(project, member_user):
                    failed.append(
                        {
                            "user": str(member_data["user"]),
                            "email": member_user.email,
                            "error": "User is already a project member.",
                        }
                    )
                    continue

                # Create membership
                ProjectMember.objects.create(
                    project=project,
                    user=member_user,
                    role=role,
                )
                added.append(str(member_data["user"]))

            except ProjectMemberNotFound:
                failed.append(
                    {
                        "user": str(member_data["user"]),
                        "error": "User not found.",
                    }
                )

        self.logger.info(
            "Bulk member addition complete. Project: %s, Added: %d, Failed: %d",
            project_id,
            len(added),
            len(failed),
        )

        return {
            "project": self.get_project_details(user=user, project_id=project_id),
            "added": added,
            "failed": failed,
        }

    @transaction.atomic
    def remove_member(self, user, project_id: str, member_id: uuid.UUID) -> Dict:
        """
        Remove a member from project.

        Business Rules:
        - Project managers can remove members
        - Workspace admins can remove members
        - Users can remove themselves (leave project)
        - Cannot remove the last manager

        Args:
            user: User instance (request.user) - performing the action
            project_id: Project UUID as string
            member_id: User UUID to remove

        Returns:
            Dict: Updated project detail payload

        Raises:
            ProjectNotFound: If project not found
            ProjectPermissionDenied: If user lacks permission
            ProjectMemberNotFound: If member not found
            ValidationError: If removing last manager
        """
        self.logger.info(
            "Removing member from project %s. Member: %s, By: %s",
            project_id,
            member_id,
            user.email,
        )

        # Get project
        project = self._get_project(project_id)

        # Get member user
        member_user = self._get_user(member_id)

        # Permission check
        is_self_removal = user.id == member_user.id
        is_manager = self._is_project_manager(project, user)
        is_workspace_admin = project.workspace.is_admin_or_owner(user)

        if not (is_self_removal or is_manager or is_workspace_admin):
            self.logger.warning(
                "User %s attempted to remove member without permission. Project: %s",
                user.email,
                project_id,
            )
            raise ProjectPermissionDenied(
                "You don't have permission to remove this member."
            )

        # Cannot remove last manager
        if self._is_last_manager(project, member_user):
            self.logger.warning(
                "Attempted to remove last manager. Project: %s, Member: %s",
                project_id,
                member_user.email,
            )
            raise ValidationError(
                "Cannot remove the last manager. Assign another manager first."
            )

        # Remove membership
        deleted_count, _ = ProjectMember.objects.filter(
            project=project,
            user=member_user,
        ).delete()

        if deleted_count == 0:
            self.logger.warning(
                "Member not found in project. Project: %s, Member: %s",
                project_id,
                member_user.email,
            )
            raise ProjectMemberNotFound(
                f"User {member_user.email} is not a member of this project."
            )

        self.logger.info(
            "Member removed successfully. Project: %s, Member: %s",
            project_id,
            member_user.email,
        )

        # Return updated details
        return self.get_project_details(user=user, project_id=project_id)

    @transaction.atomic
    def update_member_role(
        self, user, project_id: str, member_id: uuid.UUID, new_role: str
    ) -> Dict:
        """
        Update a member's role in project.

        Business Rules:
        - Only project manager or workspace admin can update roles
        - Cannot demote the last manager

        Args:
            user: User instance (request.user)
            project_id: Project UUID as string
            member_id: User UUID whose role to update
            new_role: New role to assign

        Returns:
            Dict: Updated project detail payload

        Raises:
            ProjectNotFound: If project not found
            ProjectPermissionDenied: If user lacks permission
            ProjectMemberNotFound: If member not found
            ValidationError: If demoting last manager
        """
        self.logger.info(
            "Updating member role. Project: %s, Member: %s, New Role: %s, By: %s",
            project_id,
            member_id,
            new_role,
            user.email,
        )

        # Get project
        project = self._get_project(project_id)

        # Verify permission
        self._verify_can_manage(project, user)

        # Get member user
        member_user = self._get_user(member_id)

        # Get membership
        membership = self._get_membership(project, member_user)

        old_role = membership.role

        # Check if demoting last manager
        if (
            old_role == ProjectMemberRole.MANAGER
            and new_role != ProjectMemberRole.MANAGER
            and self._is_last_manager(project, member_user)
        ):
            self.logger.warning(
                "Attempted to demote last manager. Project: %s, Member: %s",
                project_id,
                member_user.email,
            )
            raise ValidationError(
                "Cannot demote the last manager. Assign another manager first."
            )

        # Update role
        membership.role = new_role
        membership.save(update_fields=["role", "updated_at"])

        self.logger.info(
            "Member role updated. Project: %s, Member: %s, Role: %s -> %s",
            project_id,
            member_user.email,
            old_role,
            new_role,
        )

        # Return updated details
        return self.get_project_details(user=user, project_id=project_id)

    @transaction.atomic
    def update_member_tags(
        self, user, project_id: str, member_id: uuid.UUID, tags: List[str]
    ) -> Dict:
        """
        Update tags for a project member.

        Business Rules:
        - Only project manager or workspace admin can update tags
        - Members can update their own tags
        - Tags replace existing tags entirely

        Args:
            user: User instance (request.user)
            project_id: Project UUID as string
            member_id: User UUID whose tags to update
            tags: New list of tags

        Returns:
            Dict: Updated project detail payload

        Raises:
            ProjectNotFound: If project not found
            ProjectPermissionDenied: If user lacks permission
            ProjectMemberNotFound: If member not found
        """
        self.logger.info(
            "Updating member tags. Project: %s, Member: %s, By: %s",
            project_id,
            member_id,
            user.email,
        )

        # Get project
        project = self._get_project(project_id)

        # Get member user
        member_user = self._get_user(member_id)

        # Permission: manager, workspace admin, or self
        is_self = user.id == member_user.id
        is_manager = self._is_project_manager(project, user)
        is_workspace_admin = project.workspace.is_admin_or_owner(user)

        if not (is_self or is_manager or is_workspace_admin):
            self.logger.warning(
                "User %s attempted to update tags without permission. Project: %s",
                user.email,
                project_id,
            )
            raise ProjectPermissionDenied(
                "You don't have permission to update tags for this member."
            )

        # Get membership
        membership = self._get_membership(project, member_user)

        # Clean tags
        cleaned_tags = list(set(tag.strip() for tag in tags if tag.strip()))

        membership.tags = cleaned_tags
        membership.save(update_fields=["tags", "updated_at"])

        self.logger.info(
            "Member tags updated. Project: %s, Member: %s, Tags: %s",
            project_id,
            member_user.email,
            cleaned_tags,
        )

        # Return updated details
        return self.get_project_details(user=user, project_id=project_id)

    # =========================================================================
    # PRIVATE HELPER METHODS
    # =========================================================================

    def _get_project(self, project_id: str) -> Project:
        """
        Get project by ID with consistent error handling.

        Args:
            project_id: Project UUID as string

        Returns:
            Project: Project instance

        Raises:
            ProjectNotFound: If project doesn't exist
        """
        try:
            return Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            self.logger.warning("Project not found. ID: %s", project_id)
            raise ProjectNotFound(f"Project with id {project_id} not found")

    def _get_workspace(self, workspace_id: uuid.UUID) -> Workspace:
        """
        Get workspace by ID with consistent error handling.

        Args:
            workspace_id: Workspace UUID

        Returns:
            Workspace: Workspace instance

        Raises:
            WorkspaceNotFound: If workspace doesn't exist
        """
        try:
            return Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            self.logger.warning("Workspace not found. ID: %s", workspace_id)
            from workspaces.services import WorkspaceNotFound

            raise WorkspaceNotFound(f"Workspace with id {workspace_id} not found")

    def _get_user(self, user_id: uuid.UUID):
        """
        Get user by ID with consistent error handling.

        Args:
            user_id: User UUID

        Returns:
            User: User instance

        Raises:
            ProjectMemberNotFound: If user doesn't exist
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.logger.warning("User not found. ID: %s", user_id)
            raise ProjectMemberNotFound(f"User with id {user_id} not found")

    def _get_membership(self, project: Project, user) -> ProjectMember:
        """
        Get project membership for a user.

        Args:
            project: Project instance
            user: User instance

        Returns:
            ProjectMember: Membership instance

        Raises:
            ProjectMemberNotFound: If user is not a project member
        """
        try:
            return ProjectMember.objects.get(project=project, user=user)
        except ProjectMember.DoesNotExist:
            self.logger.warning(
                "Member not found in project. Project: %s, User: %s",
                project.id,
                user.email,
            )
            raise ProjectMemberNotFound(
                f"User {user.email} is not a member of this project."
            )

    def _get_user_membership(self, project: Project, user) -> Optional[ProjectMember]:
        """
        Get user's project membership or None if not a member.

        Args:
            project: Project instance
            user: User instance

        Returns:
            ProjectMember or None: Membership instance if found
        """
        try:
            return ProjectMember.objects.get(project=project, user=user)
        except ProjectMember.DoesNotExist:
            return None

    def _is_project_member(self, project: Project, user) -> bool:
        """
        Check if user is a project member.

        Args:
            project: Project instance
            user: User instance

        Returns:
            bool: True if user is a project member
        """
        return ProjectMember.objects.filter(project=project, user=user).exists()

    def _is_project_manager(self, project: Project, user) -> bool:
        """
        Check if user is a project manager.

        Args:
            project: Project instance
            user: User instance

        Returns:
            bool: True if user is a project manager
        """
        return ProjectMember.objects.filter(
            project=project,
            user=user,
            role=ProjectMemberRole.MANAGER,
        ).exists()

    def _is_last_manager(self, project: Project, user) -> bool:
        """
        Check if user is the last manager in the project.

        Args:
            project: Project instance
            user: User instance

        Returns:
            bool: True if user is the only manager
        """
        manager_count = ProjectMember.objects.filter(
            project=project,
            role=ProjectMemberRole.MANAGER,
        ).count()

        is_manager = ProjectMember.objects.filter(
            project=project,
            user=user,
            role=ProjectMemberRole.MANAGER,
        ).exists()

        return is_manager and manager_count <= 1

    def _verify_workspace_member(self, workspace: Workspace, user) -> None:
        """
        Verify user is a workspace member, raise if not.

        Args:
            workspace: Workspace instance
            user: User instance

        Raises:
            ProjectPermissionDenied: If user is not a workspace member
        """
        if not workspace.is_member(user):
            self.logger.warning(
                "User %s is not a member of workspace %s",
                user.email,
                workspace.id,
            )
            raise ProjectPermissionDenied(
                "You must be a workspace member to access projects."
            )

    def _verify_can_manage(self, project: Project, user) -> None:
        """
        Verify user can manage project (manager or workspace admin).

        Args:
            project: Project instance
            user: User instance

        Raises:
            ProjectPermissionDenied: If user lacks management permission
        """
        is_manager = self._is_project_manager(project, user)
        is_workspace_admin = project.workspace.is_admin_or_owner(user)

        if not (is_manager or is_workspace_admin):
            self.logger.warning(
                "User %s lacks management permission for project %s",
                user.email,
                project.id,
            )
            raise ProjectPermissionDenied(
                "Only project managers or workspace admins can perform this action."
            )

    def _validate_title_uniqueness(
        self, workspace: Workspace, title: str, exclude_id: Optional[uuid.UUID] = None
    ) -> None:
        """
        Validate that project title is unique within workspace.

        Args:
            workspace: Workspace instance
            title: Project title (already normalized)
            exclude_id: Project ID to exclude from check (for updates)

        Raises:
            ValidationError: If title already exists in workspace
        """
        queryset = Project.objects.filter(
            workspace=workspace,
            title__iexact=title,
            is_archived=False,
        )

        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        if queryset.exists():
            self.logger.warning(
                "Project title conflict. Workspace: %s, Title: %s",
                workspace.id,
                title,
            )
            raise ValidationError(
                f"Project with title '{title}' already exists in this workspace."
            )

    def _apply_status_transition(self, project: Project, new_status: str) -> None:
        """
        Apply status transition with business rules.

        Business Rules:
        - completed: Auto-set progress to 100%
        - planning: Auto-set progress to 0%
        - cancelled: Keep existing progress (historical)
        - Other transitions: No progress change

        Args:
            project: Project instance
            new_status: New status to apply
        """
        old_status = project.status
        project.status = new_status

        # Auto-update progress based on status
        if new_status == ProjectStatus.COMPLETED:
            project.progress = 100
        elif new_status == ProjectStatus.PLANNING:
            project.progress = 0

        self.logger.info(
            "Status transition applied. Project: %s, Status: %s -> %s, Progress: %d",
            project.id,
            old_status,
            new_status,
            project.progress,
        )

    def _replace_project_members(self, project: Project, members: List[Dict]) -> None:
        """
        Replace all project members with new list.

        Keeps the creator as manager. Removes all other members
        and adds the new ones. Validates workspace membership.

        Args:
            project: Project instance
            members: List of {"user": uuid, "role": str} dicts
        """
        # Get creator's membership (must be preserved)
        creator_membership = ProjectMember.objects.get(
            project=project,
            user=project.created_by,
        )

        # Remove all non-creator members
        ProjectMember.objects.filter(project=project).exclude(
            id=creator_membership.id
        ).delete()

        # Add new members
        added_count = 0
        for member_data in members:
            try:
                member_user = self._get_user(member_data["user"])

                # Skip creator (already a member)
                if member_user.id == project.created_by.id:
                    continue

                # Skip if not workspace member
                if not project.workspace.is_member(member_user):
                    continue

                # Create membership
                ProjectMember.objects.create(
                    project=project,
                    user=member_user,
                    role=member_data.get("role", ProjectMemberRole.CONTRIBUTOR),
                )
                added_count += 1

            except ProjectMemberNotFound:
                continue

        self.logger.info(
            "Project members replaced. Project: %s, New members added: %d",
            project.id,
            added_count,
        )

    # =========================================================================
    # PAYLOAD BUILDERS - Convert ORM Objects to Dicts
    # =========================================================================

    def _build_list_payload(self, project: Project) -> Dict:
        """
        Build list view payload from project instance.

        Uses lightweight properties that don't trigger additional DB queries.
        All related data must be pre-loaded via annotations.

        Args:
            project: Project instance with annotations

        Returns:
            Dict: Project list payload
        """
        return {
            "id": str(project.id),
            "title": project.title,
            "description": project.description or "",
            "status": project.status,
            "progress": project.progress,
            "start_date": (
                project.start_date.isoformat() if project.start_date else None
            ),
            "due_date": project.due_date.isoformat() if project.due_date else None,
            "is_archived": project.is_archived,
            "is_overdue": project.is_overdue,
            "is_active": project.is_active,
            "completion_summary": project.completion_summary,
            "days_remaining": project.days_remaining,
            "created_by": {
                "id": str(project.created_by.id),
                "email": project.created_by.email,
                "name": project.created_by.name,
            },
            "workspace": {
                "id": str(project.workspace.id),
                "name": project.workspace.name,
            },
            "user_role": getattr(project, "user_role", None),
            "member_count": getattr(project, "member_count", 0),
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }

    def _build_detail_payload(
        self,
        project: Project,
        user_membership: Optional[ProjectMember] = None,
        members_list: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Build detail view payload from project instance.

        Uses lightweight properties that don't trigger additional DB queries.
        All related data must be pre-loaded via select_related and prefetch_related.

        Args:
            project: Project instance with pre-loaded relations
            user_membership: Current user's membership (or None if workspace admin)
            members_list: Pre-built list of member dicts

        Returns:
            Dict: Complete project detail payload
        """
        payload = {
            "id": str(project.id),
            "title": project.title,
            "description": project.description or "",
            "status": project.status,
            "progress": project.progress,
            "start_date": (
                project.start_date.isoformat() if project.start_date else None
            ),
            "due_date": project.due_date.isoformat() if project.due_date else None,
            "is_archived": project.is_archived,
            "is_overdue": project.is_overdue,
            "is_active": project.is_active,
            "completion_summary": project.completion_summary,
            "duration_days": project.duration_days,
            "days_remaining": project.days_remaining,
            "status_color": project.status_color,
            "created_by": {
                "id": str(project.created_by.id),
                "email": project.created_by.email,
                "name": project.created_by.name,
            },
            "workspace": {
                "id": str(project.workspace.id),
                "name": project.workspace.name,
            },
            "user_role": user_membership.role if user_membership else "workspace_admin",
            "member_count": len(members_list) if members_list else 0,
            "members": members_list or [],
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }

        return payload
