"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import * as z from "zod";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
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
import { cn } from "@/lib/utils";
import { useEffect } from "react";
import { toast } from "sonner";

export const colorOptions = [
    "#FF5733",
    "#33C1FF",
    "#28A745",
    "#FFC300",
    "#8E44AD",
    "#E67E22",
    "#2ECC71",
    "#34495E",
];

const workspaceSchema = z.object({
    name: z
        .string()
        .min(2, "Workspace name must be at least 2 characters.")
        .max(80, "Workspace name must be at most 80 characters."),
    description: z
        .string()
        .max(200, "Description must be at most 200 characters.")
        .optional(),
    color: z.string().optional(),
});

export type WorkspaceForm = z.infer<typeof workspaceSchema>;

interface WorkspaceDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSubmit: (data: WorkspaceForm) => Promise<void>;
    isLoading?: boolean;
    mode?: "create" | "update";
    initialValues?: Partial<WorkspaceForm>;
}

const defaultWorkspaceValues: WorkspaceForm = {
    name: "",
    description: "",
    color: colorOptions[0],
};

export function WorkspaceDialog({
    open,
    onOpenChange,
    onSubmit,
    isLoading,
    mode = "create",
    initialValues,
}: WorkspaceDialogProps) {
    const form = useForm<WorkspaceForm>({
        resolver: zodResolver(workspaceSchema),
        defaultValues: {
            ...defaultWorkspaceValues,
            ...initialValues,
        },
    });

    useEffect(() => {
        if (!open) return;

        form.reset({
            ...defaultWorkspaceValues,
            ...initialValues,
        });
    }, [open, initialValues, form]);

    const title = mode === "update" ? "Edit Workspace" : "Create Workspace";
    const successMessage =
        mode === "update" ? "Workspace updated" : "Workspace created";
    const errorMessage =
        mode === "update"
            ? "Failed to update workspace"
            : "Failed to create workspace";
    const submitLabel = mode === "update" ? "Save changes" : "Create";
    const loadingLabel = mode === "update" ? "Saving..." : "Creating...";

    const handleSubmit = async (data: WorkspaceForm) => {
        try {
            await onSubmit(data);
            form.reset({
                ...defaultWorkspaceValues,
                ...initialValues,
            });
            toast.success(successMessage);
        } catch (error) {
            console.error(errorMessage, error);
            toast.error(errorMessage);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange} modal>
            <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="text-xl">{title}</DialogTitle>
                </DialogHeader>

                <form
                    id="workspace-form"
                    onSubmit={form.handleSubmit(handleSubmit)}
                >
                    <FieldGroup>
                        <Controller
                            name="name"
                            control={form.control}
                            render={({ field, fieldState }) => (
                                <Field data-invalid={fieldState.invalid}>
                                    <FieldLabel htmlFor="workspace-name">
                                        Workspace Name
                                    </FieldLabel>
                                    <Input
                                        {...field}
                                        id="workspace-name"
                                        aria-invalid={fieldState.invalid}
                                        placeholder="Test Workspace"
                                        autoComplete="off"
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
                            name="description"
                            control={form.control}
                            render={({ field, fieldState }) => (
                                <Field data-invalid={fieldState.invalid}>
                                    <FieldLabel htmlFor="workspace-description">
                                        Workspace Description
                                    </FieldLabel>
                                    <InputGroup>
                                        <InputGroupTextarea
                                            {...field}
                                            id="workspace-description"
                                            placeholder="For testing"
                                            rows={3}
                                            className="min-h-20 resize-none"
                                            aria-invalid={fieldState.invalid}
                                        />
                                        <InputGroupAddon align="block-end">
                                            <InputGroupText className="tabular-nums">
                                                {field.value?.length || 0}/200
                                                characters
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

                        <Controller
                            name="color"
                            control={form.control}
                            render={({ field }) => (
                                <Field>
                                    <FieldLabel>Workspace Color</FieldLabel>
                                    <div className="flex gap-3 flex-wrap pt-1">
                                        {colorOptions.map((color) => (
                                            <button
                                                key={color}
                                                type="button"
                                                onClick={() =>
                                                    field.onChange(color)
                                                }
                                                className={cn(
                                                    "w-8 h-8 rounded-full cursor-pointer hover:scale-110 transition-all duration-200",
                                                    field.value === color &&
                                                        "ring-2 ring-offset-2 ring-primary",
                                                )}
                                                style={{
                                                    backgroundColor: color,
                                                }}
                                                aria-label={`Select color ${color}`}
                                            />
                                        ))}
                                    </div>
                                </Field>
                            )}
                        />
                    </FieldGroup>

                    <DialogFooter className="mt-6 gap-2 sm:gap-0">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => {
                                form.reset({
                                    ...defaultWorkspaceValues,
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
