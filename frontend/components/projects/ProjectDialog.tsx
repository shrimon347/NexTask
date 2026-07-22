// components/projects/CreateProjectDialog.tsx
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import * as z from "zod";

import type { SelectedMember } from "@/components/projects/UserDropdown";
import { UserDropdown } from "@/components/projects/UserDropdown";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    Field,
    FieldError,
    FieldGroup,
    FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
    InputGroup,
    InputGroupAddon,
    InputGroupText,
    InputGroupTextarea,
} from "@/components/ui/input-group";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useProjects } from "@/hooks/useProject";
import { useEffect } from "react";

// =============================================================================
// Constants
// =============================================================================

const PROJECT_STATUS_OPTIONS = [
    { value: "planning", label: "Planning" },
    { value: "in_progress", label: "In Progress" },
    { value: "on_hold", label: "On Hold" },
    { value: "completed", label: "Completed" },
    { value: "cancelled", label: "Cancelled" },
] as const;

// =============================================================================
// Schema
// =============================================================================

const memberSchema = z.object({
    user: z.string().min(1, "Please select a user"),
    role: z.enum(["manager", "contributor", "viewer"]),
});

const projectSchema = z
    .object({
        title: z
            .string()
            .min(2, "Project title must be at least 2 characters.")
            .max(200, "Project title must be at most 200 characters."),
        description: z
            .string()
            .max(5000, "Description must be at most 5000 characters.")
            .optional()
            .nullable(),
        status: z
            .enum([
                "planning",
                "in_progress",
                "on_hold",
                "completed",
                "cancelled",
            ])
            .default("planning"),
        start_date: z.string().optional().nullable(),
        due_date: z.string().optional().nullable(),
        tags: z
            .string()
            .max(500, "Tags must be at most 500 characters")
            .optional()
            .nullable(),
        members: z
            .array(memberSchema)
            .max(50, "Cannot add more than 50 members")
            .optional()
            .default([]),
    })
    .refine(
        (data) => {
            if (data.start_date && data.due_date) {
                return new Date(data.due_date) >= new Date(data.start_date);
            }
            return true;
        },
        {
            message: "Due date cannot be before start date",
            path: ["due_date"],
        },
    );

export type CreateProjectFormData = z.infer<typeof projectSchema>;

// =============================================================================
// Types
// =============================================================================

interface CreateProjectDialogProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    workspaceId: string;
}

// =============================================================================
// Default Values
// =============================================================================

const DEFAULT_VALUES: CreateProjectFormData = {
    title: "",
    description: "",
    status: "planning",
    start_date: null,
    due_date: null,
    tags: "",
    members: [],
};

// =============================================================================
// Component
// =============================================================================

export const ProjectDialog = ({
    isOpen,
    onOpenChange,
    workspaceId,
}: CreateProjectDialogProps) => {
    const { isCreating, createProject } = useProjects({
        workspaceId,
        autoFetch: false,
    });

    const form = useForm<CreateProjectFormData>({
        resolver: zodResolver(projectSchema),
        defaultValues: DEFAULT_VALUES,
    });

    // Reset form when dialog opens/closes
    useEffect(() => {
        if (!isOpen) {
            form.reset(DEFAULT_VALUES);
        }
    }, [isOpen, form]);

    const members = form.watch("members") || [];

    const onSubmit = async (values: CreateProjectFormData) => {
        const cleanedData = {
            ...values,
            members: values.members?.filter((m) => m.user) || [],
        };
        try {
            await createProject(cleanedData);
            toast.success("Project created successfully");
            form.reset(DEFAULT_VALUES);
            onOpenChange(false);
        } catch (error: any) {
            toast.error(error?.data?.message || "Failed to create project");
        }
    };

    const handleAddMember = () => {
        if (members.length >= 50) return;
        form.setValue("members", [
            ...members,
            { user: "", role: "contributor" },
        ]);
    };

    const handleRemoveMember = (index: number) => {
        form.setValue(
            "members",
            members.filter((_, i) => i !== index),
        );
    };

    const handleMemberChange = (index: number, member: SelectedMember) => {
        const updatedMembers = [...members];
        updatedMembers[index] = { user: member.user, role: member.role };
        form.setValue("members", updatedMembers);
    };

    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange} modal>
            <DialogContent className="sm:max-w-[560px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Create Project</DialogTitle>
                    <DialogDescription>
                        Create a new project to get started
                    </DialogDescription>
                </DialogHeader>

                <form
                    id="create-project-form"
                    onSubmit={form.handleSubmit(onSubmit)}
                >
                    <FieldGroup>
                        {/* ===== Project Title ===== */}
                        <Controller
                            name="title"
                            control={form.control}
                            render={({ field, fieldState }) => (
                                <Field data-invalid={fieldState.invalid}>
                                    <FieldLabel htmlFor="project-title">
                                        Project Title
                                    </FieldLabel>
                                    <Input
                                        {...field}
                                        id="project-title"
                                        aria-invalid={fieldState.invalid}
                                        placeholder="Enter project title"
                                        autoComplete="off"
                                        className="h-10"
                                        value={field.value || ""}
                                    />
                                    {fieldState.invalid && (
                                        <FieldError
                                            errors={[fieldState.error]}
                                        />
                                    )}
                                </Field>
                            )}
                        />

                        {/* ===== Project Description ===== */}
                        <Controller
                            name="description"
                            control={form.control}
                            render={({ field, fieldState }) => (
                                <Field data-invalid={fieldState.invalid}>
                                    <FieldLabel htmlFor="project-description">
                                        Description
                                    </FieldLabel>
                                    <InputGroup>
                                        <InputGroupTextarea
                                            {...field}
                                            id="project-description"
                                            placeholder="Enter project description (optional)"
                                            rows={3}
                                            className="min-h-20 resize-none"
                                            aria-invalid={fieldState.invalid}
                                            value={field.value || ""}
                                        />
                                        <InputGroupAddon align="block-end">
                                            <InputGroupText className="tabular-nums">
                                                {(field.value || "").length}
                                                /5000
                                            </InputGroupText>
                                        </InputGroupAddon>
                                    </InputGroup>
                                    {fieldState.invalid && (
                                        <FieldError
                                            errors={[fieldState.error]}
                                        />
                                    )}
                                </Field>
                            )}
                        />

                        {/* ===== Tags ===== */}
                        <Controller
                            name="tags"
                            control={form.control}
                            render={({ field, fieldState }) => (
                                <Field data-invalid={fieldState.invalid}>
                                    <FieldLabel htmlFor="project-tags">
                                        Tags
                                    </FieldLabel>
                                    <Input
                                        {...field}
                                        id="project-tags"
                                        placeholder="e.g., frontend, api, urgent (comma-separated)"
                                        autoComplete="off"
                                        className="h-10"
                                        value={field.value || ""}
                                    />
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Separate tags with commas.
                                    </p>
                                    {fieldState.invalid && (
                                        <FieldError
                                            errors={[fieldState.error]}
                                        />
                                    )}
                                </Field>
                            )}
                        />

                        {/* ===== Status ===== */}
                        <Controller
                            name="status"
                            control={form.control}
                            render={({ field, fieldState }) => (
                                <Field data-invalid={fieldState.invalid}>
                                    <FieldLabel>Status</FieldLabel>
                                    <Select
                                        onValueChange={field.onChange}
                                        value={field.value}
                                    >
                                        <SelectTrigger className="w-full h-10">
                                            <SelectValue placeholder="Select status" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {PROJECT_STATUS_OPTIONS.map((s) => (
                                                <SelectItem
                                                    key={s.value}
                                                    value={s.value}
                                                >
                                                    {s.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    {fieldState.invalid && (
                                        <FieldError
                                            errors={[fieldState.error]}
                                        />
                                    )}
                                </Field>
                            )}
                        />

                        {/* ===== Start Date & Due Date ===== */}
                        <div className="grid grid-cols-2 gap-4">
                            <Controller
                                name="start_date"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel htmlFor="start-date">
                                            Start Date
                                        </FieldLabel>
                                        <Input
                                            type="date"
                                            id="start-date"
                                            value={field.value || ""}
                                            onChange={(e) =>
                                                field.onChange(
                                                    e.target.value || null,
                                                )
                                            }
                                            className="h-10"
                                        />
                                        {fieldState.invalid && (
                                            <FieldError
                                                errors={[fieldState.error]}
                                            />
                                        )}
                                    </Field>
                                )}
                            />
                            <Controller
                                name="due_date"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel htmlFor="due-date">
                                            Due Date
                                        </FieldLabel>
                                        <Input
                                            type="date"
                                            id="due-date"
                                            value={field.value || ""}
                                            onChange={(e) =>
                                                field.onChange(
                                                    e.target.value || null,
                                                )
                                            }
                                            className="h-10"
                                        />
                                        {fieldState.invalid && (
                                            <FieldError
                                                errors={[fieldState.error]}
                                            />
                                        )}
                                    </Field>
                                )}
                            />
                        </div>

                        {/* ===== Members ===== */}
                        <Field>
                            <FieldLabel>Team Member</FieldLabel>

                            <UserDropdown
                                value={{
                                    user: form.watch("members.0.user") || "",
                                    role:
                                        form.watch("members.0.role") ||
                                        "contributor",
                                }}
                                workspaceId={workspaceId}
                                placeholder="Select a team member..."
                                onChange={(member) => {
                                    form.setValue("members", [member], {
                                        shouldDirty: true,
                                        shouldValidate: true,
                                    });
                                }}
                            />

                            <FieldError
                                errors={[form.formState.errors.members]}
                            />
                        </Field>
                    </FieldGroup>

                    <DialogFooter className="mt-6 gap-2 sm:gap-0">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => {
                                form.reset(DEFAULT_VALUES);
                                onOpenChange(false);
                            }}
                            disabled={isCreating}
                        >
                            Cancel
                        </Button>
                        <Button type="submit" disabled={isCreating}>
                            {isCreating ? "Creating..." : "Create Project"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
};
