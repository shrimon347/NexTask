"use client";

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
import { useWorkspace } from "@/hooks/useWorkspace";
import {
    ArrowLeft,
    Calendar,
    Edit,
    FolderOpen,
    PlusCircle,
    Trash2,
    Users,
} from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

export default function WorkspaceDetailPage() {
    const params = useParams();
    const router = useRouter();
    const workspaceId = params?.workspaceId as string;

    const [isEditingWorkspace, setIsEditingWorkspace] = useState(false);
    // const [isCreatingProject, setIsCreatingProject] = useState(false);

    const {
        workspaceDetail,
        selectedWorkspace,
        isLoading,
        isWorkspaceDetailLoading,
        isUpdating,
        deleteWorkspace,
        updateWorkspace,
    } = useWorkspace(workspaceId);

    const handleDelete = async () => {
        if (confirm("Are you sure you want to delete this workspace?")) {
            await deleteWorkspace(workspaceId);
            router.push("/workspaces");
        }
    };

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

    const workspace = workspaceDetail || selectedWorkspace;
    const members = workspaceDetail?.members || [];
    const projectCount = workspaceDetail?.project_count || 0;

    if (isLoading || isWorkspaceDetailLoading) {
        return (
            <div className="flex items-center justify-center h-[60vh]">
                <p className="text-muted-foreground">Loading workspace...</p>
            </div>
        );
    }

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

    return (
        <div >
            {/* Header - same as before */}
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
                                onClick={handleDelete}
                            >
                                <Trash2 className="h-4 w-4" />
                                Delete
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content - same as before */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Content - Projects */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold">Projects</h2>
                            <Button
                                variant="outline"
                                className="gap-2"
                                onClick={() => setIsCreatingProject(true)}
                            >
                                <PlusCircle className="h-4 w-4" />
                                Create Project
                            </Button>
                        </div>

                        {projectCount === 0 ? (
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
                                        onClick={() =>
                                            setIsCreatingProject(true)
                                        }
                                    >
                                        <PlusCircle className="h-4 w-4" />
                                        Create Project
                                    </Button>
                                </CardContent>
                            </Card>
                        ) : (
                            <div className="grid gap-4">
                                {/* Project cards will go here */}
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
                onSubmit={async (data) => {
                    await updateWorkspace(workspaceId, data);
                    setIsEditingWorkspace(false);
                }}
                isLoading={isUpdating}
                mode="update"
                initialValues={{
                    name: workspace.name,
                    description: workspace.description,
                    color: workspace.color,
                }}
            />

            {/* <CreateProjectDialog
                open={isCreatingProject}
                onOpenChange={setIsCreatingProject}
                workspaceId={workspaceId}
                onSubmit={async (data) => {
                    setIsCreatingProject(false);
                }}
                isLoading={false}
            /> */}
        </div>
    );
}
