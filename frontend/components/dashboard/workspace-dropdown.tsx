"use client";

import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuGroup,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { WorkspaceAvatar } from "@/components/workspaces/workspace-avatar";
import { WorkspaceDialog } from "@/components/workspaces/WorkspaceDialog";
import { useWorkspace } from "@/hooks/useWorkspace";
import { ChevronDown, PlusCircle, XCircle } from "lucide-react";
import { useState } from "react";

export function WorkspaceDropdown() {
    const [dialogOpen, setDialogOpen] = useState(false);

    const {
        workspaces,
        selectedWorkspace,
        isLoading,
        isCreating,
        selectWorkspace,
        createWorkspace,
        clearWorkspaceSelection,
    } = useWorkspace();

    const handleCreateWorkspace = async (data: {
        name: string;
        description?: string;
    }) => {
        await createWorkspace(data);
        setDialogOpen(false);
    };

    const hasWorkspaces = workspaces.length > 0;

    return (
        <>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button
                        variant="outline"
                        className="min-w-[200px] justify-between gap-2"
                    >
                        <span className="flex items-center gap-2 min-w-0">
                            {selectedWorkspace ? (
                                <>
                                    <WorkspaceAvatar
                                        color={
                                            selectedWorkspace.color || "#6366f1"
                                        }
                                        name={selectedWorkspace.name}
                                        size="sm"
                                    />
                                    <span className="font-medium truncate max-w-[120px]">
                                        {selectedWorkspace.name}
                                    </span>
                                </>
                            ) : (
                                <span className="text-muted-foreground">
                                    {isLoading
                                        ? "Loading..."
                                        : hasWorkspaces
                                          ? "Select Workspace"
                                          : "No Workspaces"}
                                </span>
                            )}
                        </span>
                        <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
                    </Button>
                </DropdownMenuTrigger>

                <DropdownMenuContent className="w-50" align="start">
                    {/* Workspaces Label */}
                    <DropdownMenuGroup>
                        <DropdownMenuLabel>Workspaces</DropdownMenuLabel>
                    </DropdownMenuGroup>

                    <DropdownMenuSeparator />

                    {/* "Select Workspace" option to deselect */}
                    <DropdownMenuItem
                        onClick={clearWorkspaceSelection}
                        className={`flex items-center gap-2 cursor-pointer ${
                            !selectedWorkspace ? "bg-secondary" : ""
                        }`}
                    >
                        <XCircle className="h-4 w-4 text-muted-foreground" />
                        <span className="flex-1">Select Workspace</span>
                        {!selectedWorkspace && (
                            <span className="text-xs text-primary">✓</span>
                        )}
                    </DropdownMenuItem>

                    <DropdownMenuSeparator />

                    {/* Workspace list */}
                    {isLoading ? (
                        <DropdownMenuItem
                            disabled
                            className="text-muted-foreground"
                        >
                            Loading workspaces...
                        </DropdownMenuItem>
                    ) : !hasWorkspaces ? (
                        <DropdownMenuItem
                            disabled
                            className="text-muted-foreground"
                        >
                            No workspaces yet
                        </DropdownMenuItem>
                    ) : (
                        workspaces.map((ws) => (
                            <DropdownMenuItem
                                key={ws.id}
                                onClick={() => selectWorkspace(ws)}
                                className={`flex items-center gap-2 cursor-pointer ${
                                    selectedWorkspace?.id === ws.id
                                        ? "bg-secondary"
                                        : ""
                                }`}
                            >
                                <WorkspaceAvatar
                                    color={ws.color || "#6366f1"}
                                    name={ws.name}
                                    size="sm"
                                />
                                <span className="flex-1 truncate">
                                    {ws.name}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                    {ws.member_count || 0}
                                </span>
                                {selectedWorkspace?.id === ws.id && (
                                    <span className="text-xs text-primary">
                                        ✓
                                    </span>
                                )}
                            </DropdownMenuItem>
                        ))
                    )}

                    <DropdownMenuSeparator />

                    <DropdownMenuItem
                        onClick={() => setDialogOpen(true)}
                        className="text-primary cursor-pointer"
                    >
                        <PlusCircle className="h-4 w-4 mr-2" />
                        Create Workspace
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            <WorkspaceDialog
                open={dialogOpen}
                onOpenChange={setDialogOpen}
                onSubmit={handleCreateWorkspace}
                isLoading={isCreating}
                mode="create"
            />
        </>
    );
}
