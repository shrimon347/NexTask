"""
Project Management API URLs
"""

from django.urls import path

from .views import (
    ProjectArchiveView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectMemberAddView,
    ProjectMemberBulkAddView,
    ProjectMemberRemoveView,
    ProjectMemberUpdateRoleView,
    ProjectMemberUpdateTagsView,
    ProjectProgressUpdateView,
    ProjectStatusUpdateView,
)

app_name = "projects"

urlpatterns = [
    # Project CRUD (nested under workspace)
    path(
        "workspaces/<uuid:workspace_id>/projects/",
        ProjectListCreateView.as_view(),
        name="project-list-create",
    ),
    # Project detail, update, delete
    path(
        "projects/<uuid:project_id>/",
        ProjectDetailView.as_view(),
        name="project-detail",
    ),
    # Project status & progress
    path(
        "projects/<uuid:project_id>/status/",
        ProjectStatusUpdateView.as_view(),
        name="project-status-update",
    ),
    path(
        "projects/<uuid:project_id>/progress/",
        ProjectProgressUpdateView.as_view(),
        name="project-progress-update",
    ),
    # Project archive
    path(
        "projects/<uuid:project_id>/archive/",
        ProjectArchiveView.as_view(),
        name="project-archive",
    ),
    # Project members
    path(
        "projects/<uuid:project_id>/members/add/",
        ProjectMemberAddView.as_view(),
        name="project-member-add",
    ),
    path(
        "projects/<uuid:project_id>/members/bulk-add/",
        ProjectMemberBulkAddView.as_view(),
        name="project-member-bulk-add",
    ),
    path(
        "projects/<uuid:project_id>/members/remove/",
        ProjectMemberRemoveView.as_view(),
        name="project-member-remove",
    ),
    path(
        "projects/<uuid:project_id>/members/role/",
        ProjectMemberUpdateRoleView.as_view(),
        name="project-member-update-role",
    ),
    path(
        "projects/<uuid:project_id>/members/tags/",
        ProjectMemberUpdateTagsView.as_view(),
        name="project-member-update-tags",
    ),
]
