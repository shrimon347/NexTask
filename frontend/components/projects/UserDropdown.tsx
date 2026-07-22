// components/projects/UserDropdown.tsx
"use client";

import { useMemo, useState } from "react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useGetWorkspaceMembersForDropdownQuery } from "@/redux/services/projectApiSlice";
import { Check, ChevronDown, ChevronsUpDown, X } from "lucide-react";

// =============================================================================
// Constants
// =============================================================================

const PROJECT_ROLE_OPTIONS = [
    { value: "manager", label: "Manager", color: "bg-violet-500" },
    { value: "contributor", label: "Contributor", color: "bg-blue-500" },
    { value: "viewer", label: "Viewer", color: "bg-slate-400" },
] as const;

// =============================================================================
// Types
// =============================================================================

export interface SelectedMember {
    user: string;
    role: string;
    name?: string;
    email?: string;
    profile_picture?: string | null;
}

interface UserDropdownProps {
    value: SelectedMember;
    onChange: (member: SelectedMember) => void;
    workspaceId: string;
    placeholder?: string;
    disabled?: boolean;
    error?: string;
}

// =============================================================================
// Helpers
// =============================================================================

const getInitials = (name: string): string => {
    if (!name) return "U";
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
    return (
        parts[0].charAt(0) + parts[parts.length - 1].charAt(0)
    ).toUpperCase();
};

const getRole = (role: string) => {
    return (
        PROJECT_ROLE_OPTIONS.find((item) => item.value === role) ??
        PROJECT_ROLE_OPTIONS[1]
    );
};

const getRoleColor = (role: string) => getRole(role).color;
const getRoleLabel = (role: string) => getRole(role).label;

// =============================================================================
// Component
// =============================================================================

export function UserDropdown({
    value,
    onChange,
    workspaceId,
    placeholder = "Select member...",
    disabled = false,
    error,
}: UserDropdownProps) {
    const [open, setOpen] = useState(false);

    const { data: members = [], isFetching } =
        useGetWorkspaceMembersForDropdownQuery(
            { workspaceId },
            { skip: !workspaceId || !open },
        );

    const selectedUser = useMemo(
        () => members.find((m) => m.id === value.user),
        [members, value.user],
    );

    // =========================================================================
    // Event Handlers
    // =========================================================================

    const handleSelectUser = (user: (typeof members)[number]) => {
        onChange({
            user: user.id,
            role: value.role || "contributor",
            name: user.name,
            email: user.email,
            profile_picture: user.profile_picture,
        });
        setOpen(false);
    };

    const handleRoleChange = (role: string) => {
        onChange({ ...value, role });
    };

    const handleClear = (
        e: React.MouseEvent<HTMLButtonElement | SVGSVGElement>,
    ) => {
        e.stopPropagation();
        onChange({ user: "", role: "contributor" });
    };

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    type="button"
                    variant="outline"
                    role="combobox"
                    aria-expanded={open}
                    disabled={disabled}
                    className={cn(
                        "h-10 w-full justify-between rounded-lg",
                        "border-input bg-background px-3",
                        "font-normal",
                        error &&
                            "border-destructive focus-visible:ring-destructive",
                    )}
                >
                    {selectedUser ? (
                        <div className="flex min-w-0 items-center gap-2">
                            <Avatar className="h-7 w-7">
                                <AvatarImage
                                    src={selectedUser.profile_picture ?? ""}
                                />
                                <AvatarFallback className="bg-primary/10 text-xs text-primary">
                                    {getInitials(selectedUser.name)}
                                </AvatarFallback>
                            </Avatar>
                            <div className="min-w-0 text-left">
                                <p className="truncate text-sm font-medium leading-none">
                                    {selectedUser.name}
                                </p>
                                <p className="mt-1 truncate text-xs text-muted-foreground">
                                    {getRoleLabel(value.role)}
                                </p>
                            </div>
                        </div>
                    ) : (
                        <span className="text-sm text-muted-foreground">
                            {placeholder}
                        </span>
                    )}
                    <div className="ml-2 flex items-center gap-1">
                        {selectedUser && (
                            <X
                                className="h-4 w-4 cursor-pointer text-muted-foreground hover:text-foreground"
                                onClick={handleClear}
                            />
                        )}
                        <ChevronsUpDown className="h-4 w-4 opacity-50" />
                    </div>
                </Button>
            </PopoverTrigger>
            <PopoverContent align="start" className="w-[420px] p-0">
                <Command>
                    <CommandInput placeholder="Search members..." />
                    <CommandList className="max-h-[320px]">
                        {isFetching && (
                            <div className="py-8 text-center text-sm text-muted-foreground">
                                Loading members...
                            </div>
                        )}
                        {!isFetching && members.length === 0 && (
                            <CommandEmpty>
                                No workspace members found.
                            </CommandEmpty>
                        )}
                        {!isFetching && members.length > 0 && (
                            <CommandGroup heading="Workspace Members">
                                {members.map((user) => {
                                    const isSelected = value.user === user.id;
                                    return (
                                        <CommandItem
                                            key={user.id}
                                            value={`${user.name} ${user.email}`}
                                            onSelect={() =>
                                                handleSelectUser(user)
                                            }
                                            className={cn(
                                                "group flex items-center gap-3 rounded-md px-2 py-2 cursor-pointer",
                                                "hover:bg-accent/60",
                                                isSelected && "bg-accent",
                                            )}
                                        >
                                            <Check
                                                className={cn(
                                                    "h-4 w-4 shrink-0 transition-opacity",
                                                    isSelected
                                                        ? "opacity-100 text-primary"
                                                        : "opacity-0",
                                                )}
                                            />
                                            <Avatar className="h-8 w-8 shrink-0">
                                                <AvatarImage
                                                    src={
                                                        user.profile_picture ??
                                                        ""
                                                    }
                                                />
                                                <AvatarFallback className="bg-primary/10 text-xs text-primary">
                                                    {getInitials(user.name)}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div className="min-w-0 flex-1">
                                                <div className="truncate text-sm font-medium">
                                                    {user.name}
                                                </div>
                                                <div className="truncate text-xs text-muted-foreground">
                                                    {user.email}
                                                </div>
                                            </div>
                                            <Select
                                                value={
                                                    isSelected
                                                        ? value.role
                                                        : "contributor"
                                                }
                                                onValueChange={(role) => {
                                                    if (isSelected) {
                                                        handleRoleChange(role);
                                                    } else {
                                                        onChange({
                                                            user: user.id,
                                                            role,
                                                            name: user.name,
                                                            email: user.email,
                                                            profile_picture:
                                                                user.profile_picture,
                                                        });
                                                    }
                                                }}
                                            >
                                                <SelectTrigger
                                                    onClick={(e) =>
                                                        e.stopPropagation()
                                                    }
                                                    className={cn(
                                                        "ml-auto h-8 w-auto min-w-[115px]",
                                                        "border-0 bg-transparent",
                                                        "shadow-none",
                                                        "px-2",
                                                        "text-xs font-medium",
                                                        "hover:bg-muted",
                                                        "focus:ring-0 focus:ring-offset-0",
                                                    )}
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <span
                                                            className={cn(
                                                                "h-2 w-2 rounded-full",
                                                                getRoleColor(
                                                                    isSelected
                                                                        ? value.role
                                                                        : "contributor",
                                                                ),
                                                            )}
                                                        />
                                                        <SelectValue />
                                                        <ChevronDown className="h-3 w-3 opacity-60" />
                                                    </div>
                                                </SelectTrigger>
                                                <SelectContent align="end">
                                                    {PROJECT_ROLE_OPTIONS.map(
                                                        (role) => (
                                                            <SelectItem
                                                                key={role.value}
                                                                value={
                                                                    role.value
                                                                }
                                                            >
                                                                <div className="flex items-center gap-2">
                                                                    <span
                                                                        className={cn(
                                                                            "h-2 w-2 rounded-full",
                                                                            role.color,
                                                                        )}
                                                                    />
                                                                    {role.label}
                                                                </div>
                                                            </SelectItem>
                                                        ),
                                                    )}
                                                </SelectContent>
                                            </Select>
                                        </CommandItem>
                                    );
                                })}
                            </CommandGroup>
                        )}
                    </CommandList>
                </Command>
            </PopoverContent>
        </Popover>
    );
}
