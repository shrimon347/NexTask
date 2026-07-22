// components/projects/ProjectDialog.tsx
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useFieldArray, useForm } from "react-hook-form";
import * as z from "zod";

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
import { cn } from "@/lib/utils";
import { PlusCircle, Trash2 } from "lucide-react";
import { useEffect } from "react";

// =============================================================================
// Constants
// =============================================================================

const PROJECT_STATUS_OPTIONS = [
    { value: "planning", label: "Planning", color: "bg-blue-500" },
    { value: "in_progress", label: "In Progress", color: "bg-yellow-500" },
    { value: "on_hold", label: "On Hold", color: "bg-orange-500" },
    { value: "completed", label: "Completed", color: "bg-green-500" },
    { value: "cancelled", label: "Cancelled", color: "bg-red-500" },
] as const;

const MEMBER_ROLE_OPTIONS = [
    { value: "manager", label: "Manager" },
    { value: "contributor", label: "Contributor" },
    { value: "viewer", label: "Viewer" },
] as const;

// =============================================================================
// Schema
// =============================================================================

const memberSchema = z.object({
    user: z.string().min(1, "User ID is required"),
    role: z.enum(["manager", "contributor", "viewer"]).default("contributor"),
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
        progress: z
            .number()
            .min(0, "Progress cannot be less than 0%")
            .max(100, "Progress cannot exceed 100%")
            .default(0),
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
            // Validate progress matches status
            if (data.status === "planning" && data.progress > 0) {
                return false;
            }
            if (data.status === "completed" && data.progress < 100) {
                return false;
            }
            return true;
        },
        {
            message:
                "Progress must be 0% for planning and 100% for completed projects",
            path: ["progress"],
        },
    )
    .refine(
        (data) => {
            // Validate due date is after start date
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

export type ProjectForm = z.infer<typeof projectSchema>;

// =============================================================================
// Types
// =============================================================================

interface ProjectDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSubmit: (data: ProjectForm) => Promise<void>;
    isLoading?: boolean;
    mode?: "create" | "update";
    initialValues?: Partial<ProjectForm>;
}

// =============================================================================
// Default Values
// =============================================================================

const DEFAULT_VALUES: ProjectForm = {
    title: "",
    description: "",
    status: "planning",
    start_date: null,
    due_date: null,
    progress: 0,
    tags: "",
    members: [],
};

// =============================================================================
// Component
// =============================================================================

export function ProjectDialog({
    open,
    onOpenChange,
    onSubmit,
    isLoading = false,
    mode = "create",
    initialValues,
}: ProjectDialogProps) {
    const isUpdate = mode === "update";

    const form = useForm<ProjectForm>({
        resolver: zodResolver(projectSchema),
        defaultValues: { ...DEFAULT_VALUES, ...initialValues },
    });

    const { fields, append, remove } = useFieldArray({
        control: form.control,
        name: "members",
    });

    // Reset form when dialog opens
    useEffect(() => {
        if (!open) return;
        form.reset({ ...DEFAULT_VALUES, ...initialValues });
    }, [open, initialValues, form]);

    // Watch status for conditional progress
    const currentStatus = form.watch("status");

    const handleSubmit = async (data: ProjectForm) => {
        await onSubmit(data);
    };

    const handleAddMember = () => {
        if (fields.length >= 50) return;
        append({ user: "", role: "contributor" });
    };

    // ============ Labels ============
    const title = isUpdate ? "Edit Project" : "Create Project";
    const description = isUpdate
        ? "Update the project details below."
        : "Fill in the details to create a new project.";
    const submitLabel = isUpdate ? "Save Changes" : "Create Project";
    const loadingLabel = isUpdate ? "Saving..." : "Creating...";

    return (
        <Dialog open={open} onOpenChange={onOpenChange} modal>
            <DialogContent className="sm:max-w-[560px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="text-xl">{title}</DialogTitle>
                    <DialogDescription>{description}</DialogDescription>
                </DialogHeader>

                <form
                    id="project-form"
                    onSubmit={form.handleSubmit(handleSubmit)}
                >
                    <FieldGroup>
                        {/* ===== Project Title ===== */}
                        <Controller
                            name="title"
                            control={form.control}
                            render={({ field, fieldState }) => (
                                <Field data-invalid={fieldState.invalid}>
                                    <FieldLabel
                                        htmlFor="project-title"
                                        required
                                    >
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
                                        Separate tags with commas. Applied to
                                        your membership.
                                    </p>
                                    {fieldState.invalid && (
                                        <FieldError
                                            errors={[fieldState.error]}
                                        />
                                    )}
                                </Field>
                            )}
                        />

                        {/* ===== Status & Progress ===== */}
                        <div className="grid grid-cols-1">
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
                                                {PROJECT_STATUS_OPTIONS.map(
                                                    (status) => (
                                                        <SelectItem
                                                            key={status.value}
                                                            value={status.value}
                                                        >
                                                            <div className="flex items-center gap-2">
                                                                <span
                                                                    className={cn(
                                                                        "h-2 w-2 rounded-full",
                                                                        status.color,
                                                                    )}
                                                                />
                                                                {status.label}
                                                            </div>
                                                        </SelectItem>
                                                    ),
                                                )}
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
                        </div>

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
                                            onChange={(e) => {
                                                const value = e.target.value;
                                                field.onChange(value || null);
                                            }}
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
                                            onChange={(e) => {
                                                const value = e.target.value;
                                                field.onChange(value || null);
                                            }}
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
                            <div className="flex items-center justify-between mb-2">
                                <FieldLabel>Team Members</FieldLabel>
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    className="gap-1 h-8"
                                    onClick={handleAddMember}
                                    disabled={fields.length >= 50}
                                >
                                    <PlusCircle className="h-3.5 w-3.5" />
                                    Add Member
                                </Button>
                            </div>

                            {fields.length === 0 ? (
                                <div className="text-center py-4 border border-dashed rounded-lg">
                                    <p className="text-sm text-muted-foreground">
                                        No members added yet. Add team members
                                        to collaborate.
                                    </p>
                                </div>
                            ) : (
                                <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
                                    {fields.map((memberField, index) => (
                                        <div
                                            key={memberField.id}
                                            className="flex items-center gap-2 p-2 border rounded-lg bg-muted/30"
                                        >
                                            <Controller
                                                name={`members.${index}.user`}
                                                control={form.control}
                                                render={({
                                                    field,
                                                    fieldState,
                                                }) => (
                                                    <div className="flex-1 min-w-0">
                                                        <Input
                                                            {...field}
                                                            placeholder="User ID (UUID)"
                                                            className="h-9 text-sm"
                                                            aria-invalid={
                                                                fieldState.invalid
                                                            }
                                                        />
                                                        {fieldState.invalid && (
                                                            <p className="text-xs text-destructive mt-0.5">
                                                                {
                                                                    fieldState
                                                                        .error
                                                                        ?.message
                                                                }
                                                            </p>
                                                        )}
                                                    </div>
                                                )}
                                            />
                                            <Controller
                                                name={`members.${index}.role`}
                                                control={form.control}
                                                render={({ field }) => (
                                                    <Select
                                                        onValueChange={
                                                            field.onChange
                                                        }
                                                        value={field.value}
                                                    >
                                                        <SelectTrigger className="w-[130px] h-9 shrink-0">
                                                            <SelectValue />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            {MEMBER_ROLE_OPTIONS.map(
                                                                (role) => (
                                                                    <SelectItem
                                                                        key={
                                                                            role.value
                                                                        }
                                                                        value={
                                                                            role.value
                                                                        }
                                                                    >
                                                                        {
                                                                            role.label
                                                                        }
                                                                    </SelectItem>
                                                                ),
                                                            )}
                                                        </SelectContent>
                                                    </Select>
                                                )}
                                            />
                                            <Button
                                                type="button"
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive"
                                                onClick={() => remove(index)}
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {fields.length > 0 && (
                                <p className="text-xs text-muted-foreground mt-2">
                                    {fields.length}/50 members added. Members
                                    must be workspace members first.
                                </p>
                            )}
                        </Field>
                    </FieldGroup>

                    {/* ===== Footer ===== */}
                    <DialogFooter className="mt-6 gap-2 sm:gap-0">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => {
                                form.reset({
                                    ...DEFAULT_VALUES,
                                    ...initialValues,
                                });
                                onOpenChange(false);
                            }}
                            disabled={isLoading}
                        >
                            Cancel
                        </Button>
                        <Button type="submit" disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                                    {loadingLabel}
                                </>
                            ) : (
                                submitLabel
                            )}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

// =============================================================================
// Re-export for EditProjectDialog
// =============================================================================

export { MEMBER_ROLE_OPTIONS, PROJECT_STATUS_OPTIONS, projectSchema };
export type { ProjectDialogProps };
