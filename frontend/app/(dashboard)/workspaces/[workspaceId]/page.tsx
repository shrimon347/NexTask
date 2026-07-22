"use client";

import type { ProjectForm } from "@/components/projects/ProjectDialog";
import { ProjectDialog } from "@/components/projects/ProjectDialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { WorkspaceDialog } from "@/components/workspaces/WorkspaceDialog";
import { WorkspaceAvatar } from "@/components/workspaces/workspace-avatar";
import { useProjects } from "@/hooks/useProject";
import { useWorkspace } from "@/hooks/useWorkspace";
import { cn } from "@/lib/utils";
import type { ProjectListItem } from "@/redux/services/projectApiSlice";
import {
    AlertCircle,
    ArrowLeft,
    Calendar,
    CheckCircle,
    Clock,
    Edit,
    FolderOpen,
    PlusCircle,
    Trash2,
    Users,
    XCircle,
} from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

const statusConfig = {
    planning: { label: "Planning", color: "bg-blue-500", icon: Clock },
    in_progress: {
        label: "In Progress",
        color: "bg-yellow-500",
        icon: AlertCircle,
    },
    on_hold: { label: "On Hold", color: "bg-orange-500", icon: AlertCircle },
    completed: { label: "Completed", color: "bg-green-500", icon: CheckCircle },
    cancelled: { label: "Cancelled", color: "bg-red-500", icon: XCircle },
};

export default function WorkspaceDetailPage() {
    const params = useParams();
    const router = useRouter();
    const workspaceId = params?.workspaceId as string;

    // ============ State ============
    const [isEditingWorkspace, setIsEditingWorkspace] = useState(false);
    const [projectDialog, setProjectDialog] = useState<{
        open: boolean;
        mode: "create" | "update";
        project?: ProjectListItem;
    }>({ open: false, mode: "create" });

    // ============ Workspace hooks ============
    const {
        workspaceDetail,
        selectedWorkspace,
        isLoading: isWorkspaceLoading,
        isWorkspaceDetailLoading,
        isUpdating,
        deleteWorkspace,
        updateWorkspace,
    } = useWorkspace(workspaceId);

    // ============ Project hooks ============
    const {
        projects,
        isLoading: isProjectsLoading,
        isCreating,
        isUpdating: isUpdatingProject,
        createProject,
        updateProject,
        deleteProject,
    } = useProjects({
        workspaceId,
        queryParams: {
            sort_by: "created_at",
            sort_order: "desc",
            is_archived: false,
        },
    });

    // ============ Computed Values ============
    const workspace = workspaceDetail || selectedWorkspace;
    const members = workspaceDetail?.members || [];
    const projectCount = workspaceDetail?.project_count || 0;
    const isLoading =
        isWorkspaceLoading || isWorkspaceDetailLoading || isProjectsLoading;
    const isProjectDialogLoading =
        projectDialog.mode === "create" ? isCreating : isUpdatingProject;

    // ============ Handlers ============

    const handleOpenCreateDialog = () => {
        setProjectDialog({ open: true, mode: "create" });
    };

    const handleOpenEditDialog = (project: ProjectListItem) => {
        setProjectDialog({ open: true, mode: "update", project });
    };

    const handleCloseProjectDialog = () => {
        setProjectDialog((prev) => ({ ...prev, open: false }));
    };

    const handleProjectSubmit = async (data: ProjectForm) => {
        if (projectDialog.mode === "create") {
            await createProject(data);
        } else if (projectDialog.project) {
            await updateProject(projectDialog.project.id, data);
        }
        handleCloseProjectDialog();
    };

    const handleWorkspaceUpdate = async (data: any) => {
        await updateWorkspace(workspaceId, data);
        setIsEditingWorkspace(false);
    };

    const handleDeleteWorkspace = async () => {
        if (confirm("Are you sure you want to delete this workspace?")) {
            await deleteWorkspace(workspaceId);
            router.push("/workspaces");
        }
    };

    const handleDeleteProject = async (projectId: string) => {
        if (confirm("Are you sure you want to delete this project?")) {
            await deleteProject(projectId);
        }
    };

    // ============ Helpers ============

    const getInitials = (name: string) => {
        return name?.charAt(0)?.toUpperCase() || "U";
    };

    const formatDate = (date: string) => {
        return new Date(date).toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric",
        });
    };

    // ============ Loading State ============
    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-[60vh]">
                <p className="text-muted-foreground">Loading workspace...</p>
            </div>
        );
    }

    // ============ Not Found State ============
    if (!workspace) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh] text-center">
                <p className="text-muted-foreground">Workspace not found</p>
                <Button
                    variant="outline"
                    onClick={() => router.push("/workspaces")}
                    className="mt-4"
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Workspaces
                </Button>
            </div>
        );
    }

    // ============ Main Render ============
    return (
        <div>
            {/* Header */}
            <div className="border-b bg-card">
                <div className="mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <Button
                        variant="ghost"
                        onClick={() => router.push("/workspaces")}
                        className="gap-2 -ml-3 mb-4"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to Workspaces
                    </Button>

                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                        <div className="flex items-start gap-4">
                            <WorkspaceAvatar
                                color={workspace.color || "#6366f1"}
                                name={workspace.name}
                                size="lg"
                            />
                            <div>
                                <h1 className="text-2xl font-bold">
                                    {workspace.name}
                                </h1>
                                {workspace.description && (
                                    <p className="text-muted-foreground mt-1">
                                        {workspace.description}
                                    </p>
                                )}
                                <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                                    <span className="flex items-center gap-1">
                                        <Users className="h-4 w-4" />
                                        {workspace.member_count || 0} Members
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <FolderOpen className="h-4 w-4" />
                                        {projectCount} Projects
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <Calendar className="h-4 w-4" />
                                        Created{" "}
                                        {formatDate(workspace.created_at)}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                className="gap-2"
                                onClick={() => setIsEditingWorkspace(true)}
                            >
                                <Edit className="h-4 w-4" />
                                Edit
                            </Button>
                            <Button
                                variant="destructive"
                                className="gap-2"
                                onClick={handleDeleteWorkspace}
                            >
                                <Trash2 className="h-4 w-4" />
                                Delete
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Content - Projects */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold">Projects</h2>
                            <Button
                                variant="outline"
                                className="gap-2"
                                onClick={handleOpenCreateDialog}
                            >
                                <PlusCircle className="h-4 w-4" />
                                Create Project
                            </Button>
                        </div>

                        {projects.length === 0 ? (
                            <Card className="border-dashed border-2 bg-muted/20">
                                <CardHeader>
                                    <CardTitle className="text-lg">
                                        No projects yet
                                    </CardTitle>
                                    <CardDescription>
                                        Get started by creating your first
                                        project in this workspace
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <Button
                                        variant="default"
                                        className="gap-2"
                                        onClick={handleOpenCreateDialog}
                                    >
                                        <PlusCircle className="h-4 w-4" />
                                        Create Project
                                    </Button>
                                </CardContent>
                            </Card>
                        ) : (
                            <div className="grid gap-4">
                                {projects.map((project) => {
                                    const status =
                                        statusConfig[project.status] ||
                                        statusConfig.planning;
                                    const StatusIcon = status.icon;

                                    return (
                                        <Card
                                            key={project.id}
                                            className="hover:shadow-md transition-shadow cursor-pointer"
                                            onClick={() =>
                                                router.push(
                                                    `/projects/${project.id}`,
                                                )
                                            }
                                        >
                                            <CardHeader className="flex flex-row items-start justify-between">
                                                <div className="space-y-1">
                                                    <CardTitle className="text-lg">
                                                        {project.title}
                                                    </CardTitle>
                                                    {project.description && (
                                                        <CardDescription className="line-clamp-2">
                                                            {
                                                                project.description
                                                            }
                                                        </CardDescription>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span
                                                        className={cn(
                                                            "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium text-white",
                                                            status.color,
                                                        )}
                                                    >
                                                        <StatusIcon className="h-3 w-3" />
                                                        {status.label}
                                                    </span>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleOpenEditDialog(
                                                                project,
                                                            );
                                                        }}
                                                    >
                                                        <Edit className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="text-destructive hover:text-destructive"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDeleteProject(
                                                                project.id,
                                                            );
                                                        }}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                                    <span>
                                                        Progress:{" "}
                                                        {project.progress}%
                                                    </span>
                                                    {project.due_date && (
                                                        <span>
                                                            Due:{" "}
                                                            {formatDate(
                                                                project.due_date,
                                                            )}
                                                        </span>
                                                    )}
                                                    <span>
                                                        {project.member_count}{" "}
                                                        members
                                                    </span>
                                                    {project.is_overdue && (
                                                        <span className="text-destructive font-medium">
                                                            Overdue
                                                        </span>
                                                    )}
                                                </div>
                                                {project.progress > 0 && (
                                                    <div className="mt-2 h-1.5 w-full bg-muted rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-primary transition-all"
                                                            style={{
                                                                width: `${project.progress}%`,
                                                            }}
                                                        />
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {/* Sidebar - Members */}
                    <div className="space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <Users className="h-5 w-5" />
                                    Members
                                </CardTitle>
                                <CardDescription>
                                    {workspace.member_count || 0} member
                                    {workspace.member_count !== 1 ? "s" : ""}
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {members.length === 0 ? (
                                    <p className="text-sm text-muted-foreground">
                                        No members yet
                                    </p>
                                ) : (
                                    <div className="space-y-3">
                                        {members.map((member) => (
                                            <div
                                                key={member.id}
                                                className="flex items-center gap-3"
                                            >
                                                <Avatar className="h-8 w-8">
                                                    <AvatarImage
                                                        src={
                                                            member.profile_picture ||
                                                            ""
                                                        }
                                                    />
                                                    <AvatarFallback className="bg-primary/10 text-primary">
                                                        {getInitials(
                                                            member.name,
                                                        )}
                                                    </AvatarFallback>
                                                </Avatar>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium truncate">
                                                        {member.name}
                                                    </p>
                                                    <p className="text-xs text-muted-foreground capitalize">
                                                        {member.role}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>

            {/* Dialogs */}
            <WorkspaceDialog
                open={isEditingWorkspace}
                onOpenChange={setIsEditingWorkspace}
                onSubmit={handleWorkspaceUpdate}
                isLoading={isUpdating}
                mode="update"
                initialValues={{
                    name: workspace.name,
                    description: workspace.description,
                    color: workspace.color,
                }}
            />

            <ProjectDialog
                isOpen={projectDialog.open}
                onOpenChange={handleCloseProjectDialog}
                onSubmit={handleProjectSubmit}
                isLoading={isProjectDialogLoading}
                mode={projectDialog.mode}
                workspaceId={workspaceId}
                initialValues={
                    projectDialog.mode === "update" && projectDialog.project
                        ? {
                              title: projectDialog.project.title,
                              description:
                                  projectDialog.project.description || "",
                              status: projectDialog.project.status,
                              start_date:
                                  projectDialog.project.start_date || "",
                              due_date: projectDialog.project.due_date || "",
                              progress: projectDialog.project.progress,
                          }
                        : undefined
                }
            />
        </div>
    );
}
