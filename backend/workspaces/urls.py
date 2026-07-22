from django.urls import path

from . import views

app_name = "workspaces"

urlpatterns = [
    # Workspace CRUD
    path(
        "workspaces/",
        views.WorkspaceListCreateView.as_view(),
        name="workspace-list-create",
    ),
    path(
        "workspaces/<uuid:workspace_id>/",
        views.WorkspaceDetailView.as_view(),
        name="workspace-detail",
    ),
    # Workspace members list (for dropdown)
    path(
        "workspaces/<uuid:workspace_id>/members/dropdown/",
        views.WorkspaceMembersDropdownView.as_view(),
        name="workspace-members-deopdown",
    ),
    # Member Management
    path(
        "workspaces/<uuid:workspace_id>/members/add/",
        views.WorkspaceMemberAddView.as_view(),
        name="workspace-add-member",
    ),
    path(
        "workspaces/<uuid:workspace_id>/members/remove/",
        views.WorkspaceMemberRemoveView.as_view(),
        name="workspace-remove-member",
    ),
    path(
        "workspaces/<uuid:workspace_id>/members/update-role/",
        views.WorkspaceMemberUpdateRoleView.as_view(),
        name="workspace-update-member-role",
    ),
    # Ownership Transfer
    path(
        "workspaces/<uuid:workspace_id>/transfer-ownership/",
        views.WorkspaceTransferOwnershipView.as_view(),
        name="workspace-transfer-ownership",
    ),
]
