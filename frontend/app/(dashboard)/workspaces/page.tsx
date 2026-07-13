// app/(dashboard)/workspaces/page.tsx
"use client";

import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { CreateWorkspaceDialog } from "@/components/workspaces/CreateWorkspaceDialog";
import { WorkspaceAvatar } from "@/components/workspaces/workspace-avatar";
import { useWorkspace } from "@/hooks/useWorkspace";
import { cn } from "@/lib/utils";
import { Check, ChevronDown, PlusCircle } from "lucide-react";
import { useState } from "react";

export default function WorkspacesPage() {
    const [dialogOpen, setDialogOpen] = useState(false);

    const {
        workspaces,
        selectedWorkspace,
        isLoading,
        isCreating,
        selectWorkspace,
        createWorkspace,
    } = useWorkspace();

    const handleCreateWorkspace = async (data: {
        name: string;
        description?: string;
        color?: string;
    }) => {
        await createWorkspace(data);
        setDialogOpen(false);
    };

    const hasWorkspaces = workspaces.length > 0;

    // Show loading state
    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-[60vh]">
                <p className="text-muted-foreground">Loading workspaces...</p>
            </div>
        );
    }

    // Show empty state
    if (!hasWorkspaces) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh] text-center">
                <div className="rounded-full bg-muted p-6 mb-4">
                    <PlusCircle className="h-12 w-12 text-muted-foreground" />
                </div>
                <h2 className="text-2xl font-semibold">No workspaces found</h2>
                <p className="text-muted-foreground mt-2 max-w-md">
                    Create a new workspace to organize your projects and
                    collaborate with your team.
                </p>
                <Button
                    onClick={() => setDialogOpen(true)}
                    className="mt-6"
                    size="lg"
                >
                    <PlusCircle className="h-4 w-4 mr-2" />
                    Create Workspace
                </Button>

                <CreateWorkspaceDialog
                    open={dialogOpen}
                    onOpenChange={setDialogOpen}
                    onSubmit={handleCreateWorkspace}
                    isLoading={isCreating}
                />
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">Workspaces</h1>
                    <p className="text-muted-foreground">
                        Manage your workspaces and projects
                    </p>
                </div>
                <Button onClick={() => setDialogOpen(true)} className="gap-2">
                    <PlusCircle className="h-4 w-4" />
                    New Workspace
                </Button>
            </div>

            {/* Workspace Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {workspaces.map((ws) => (
                    <Card
                        key={ws.id}
                        className={cn(
                            "group cursor-pointer transition-all hover:shadow-lg",
                            selectedWorkspace?.id === ws.id
                                ? "border-primary bg-primary/5"
                                : "hover:border-primary/50",
                        )}
                        onClick={() => selectWorkspace(ws)}
                    >
                        <CardHeader className="flex flex-row items-start gap-4 space-y-0">
                            <WorkspaceAvatar
                                color={ws.color || "#6366f1"}
                                name={ws.name}
                                size="lg"
                            />
                            <div className="flex-1 min-w-0">
                                <div className="flex items-start justify-between">
                                    <CardTitle className="truncate">
                                        {ws.name}
                                    </CardTitle>
                                    {selectedWorkspace?.id === ws.id && (
                                        <Check className="h-4 w-4 text-primary shrink-0 mt-1" />
                                    )}
                                </div>
                                <CardDescription className="text-xs">
                                    Created{" "}
                                    {new Date(ws.created_at).toLocaleDateString(
                                        "en-US",
                                        {
                                            month: "long",
                                            day: "numeric",
                                            year: "numeric",
                                        },
                                    )}
                                </CardDescription>
                            </div>
                        </CardHeader>

                        <CardContent className="space-y-3">
                            {ws.description && (
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                    {ws.description}
                                </p>
                            )}

                            <div className="flex items-center justify-between pt-2 border-t">
                                <span className="text-xs text-muted-foreground">
                                    {ws.member_count || 1} member
                                    {ws.member_count !== 1 ? "s" : ""}
                                    {ws.role && ` · ${ws.role}`}
                                </span>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 text-xs text-muted-foreground hover:text-primary gap-1"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        selectWorkspace(ws);
                                    }}
                                >
                                    View details
                                    <ChevronDown className="h-3 w-3 rotate-[-90deg]" />
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <CreateWorkspaceDialog
                open={dialogOpen}
                onOpenChange={setDialogOpen}
                onSubmit={handleCreateWorkspace}
                isLoading={isCreating}
            />
        </div>
    );
}
