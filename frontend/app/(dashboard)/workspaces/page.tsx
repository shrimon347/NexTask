// app/(dashboard)/workspaces/page.tsx
"use client";

import { Button } from "@/components/ui/button";
import { WorkspaceCard } from "@/components/workspaces/workspace-card";
import { WorkspaceDialog } from "@/components/workspaces/WorkspaceDialog";
import { useWorkspace } from "@/hooks/useWorkspace";
import { PlusCircle } from "lucide-react";
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

                <WorkspaceDialog
                    open={dialogOpen}
                    onOpenChange={setDialogOpen}
                    onSubmit={handleCreateWorkspace}
                    isLoading={isCreating}
                    mode="create"
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
                    <WorkspaceCard
                        key={ws.id}
                        workspace={ws}
                        isSelected={selectedWorkspace?.id === ws.id}
                        onSelect={() => selectWorkspace(ws)}
                    />
                ))}
            </div>

            <WorkspaceDialog
                open={dialogOpen}
                onOpenChange={setDialogOpen}
                onSubmit={handleCreateWorkspace}
                isLoading={isCreating}
                mode="create"
            />
        </div>
    );
}
