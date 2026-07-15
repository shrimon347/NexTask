"use client";

import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { WorkspaceAvatar } from "@/components/workspaces/workspace-avatar";
import { cn } from "@/lib/utils";
import { Check, Users } from "lucide-react";

interface WorkspaceCardProps {
    workspace: {
        id: string;
        name: string;
        description?: string;
        color?: string;
        member_count?: number;
        role?: string;
        created_at: string;
    };
    isSelected?: boolean;
    onSelect: () => void;
}

export function WorkspaceCard({
    workspace,
    isSelected = false,
    onSelect,
}: WorkspaceCardProps) {
    return (
        <Card
            className={cn(
                "group cursor-pointer transition-all hover:shadow-lg",
                isSelected
                    ? "border-primary bg-primary/5"
                    : "hover:border-primary/50 bg-primary/5",
            )}
            onClick={onSelect}
        >
            <CardHeader className="flex flex-row items-start gap-4 space-y-0">
                <WorkspaceAvatar
                    color={workspace.color || "#6366f1"}
                    name={workspace.name}
                    size="lg"
                />
                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                        <CardTitle className="truncate">
                            {workspace.name}
                        </CardTitle>
                        {isSelected && (
                            <Check className="h-4 w-4 text-primary shrink-0 mt-1" />
                        )}
                    </div>
                    <CardDescription className="text-xs">
                        Created{" "}
                        {new Date(workspace.created_at).toLocaleString(
                            "en-US",
                            {
                                month: "long",
                                day: "numeric",
                                year: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                            },
                        )}
                    </CardDescription>
                </div>

                <div>
                    <span className="text-sm flex justify-center items-center gap-1 text-muted-foreground">
                        <Users className="h-3 w-3 " />
                        {workspace.member_count || 1}
                        {/* {workspace.role && ` · ${workspace.role}`} */}
                    </span>
                </div>
            </CardHeader>

            <CardContent className="space-y-3">
                {workspace.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                        {workspace.description}
                    </p>
                )}

                <div className="flex items-center justify-between pt-2">
                    <p>View workspace details and projects</p>
                </div>
            </CardContent>
        </Card>
    );
}
