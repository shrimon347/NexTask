/* eslint-disable react-hooks/incompatible-library */
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
    AlertCircle,
    ArrowLeft,
    CheckCircle,
    Eye,
    EyeOff,
    KeyRound,
    Lock,
    Shield,
    XCircle,
} from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

import { useResetPasswordConfirm } from "@/hooks/useResetPasswordConfirm";

// Password validation schema
const resetPasswordConfirmSchema = z
    .object({
        new_password: z
            .string()
            .min(8, "Password must be at least 8 characters")
            .regex(
                /[A-Z]/,
                "Password must contain at least one uppercase letter",
            )
            .regex(
                /[a-z]/,
                "Password must contain at least one lowercase letter",
            )
            .regex(/[0-9]/, "Password must contain at least one number")
            .regex(/[^A-Za-z0-9]/, "Password must contain at least one symbol"),
        re_new_password: z.string().min(1, "Please confirm your password"),
    })
    .refine((data) => data.new_password === data.re_new_password, {
        message: "Passwords do not match",
        path: ["re_new_password"],
    });

type ResetPasswordConfirmFormData = z.infer<typeof resetPasswordConfirmSchema>;

// Password strength checks
const PASSWORD_CHECKS = [
    {
        id: "length",
        label: "8+ characters",
        test: (p: string) => p.length >= 8,
    },
    {
        id: "upper",
        label: "Uppercase letter",
        test: (p: string) => /[A-Z]/.test(p),
    },
    {
        id: "lower",
        label: "Lowercase letter",
        test: (p: string) => /[a-z]/.test(p),
    },
    { id: "number", label: "Number", test: (p: string) => /[0-9]/.test(p) },
    {
        id: "symbol",
        label: "Symbol",
        test: (p: string) => /[^A-Za-z0-9]/.test(p),
    },
] as const;

interface Props {
    params: Promise<{
        uid: string;
        token: string;
    }>;
}

export default function PasswordResetConfirmPage({ params }: Props) {
    const router = useRouter();
    const {
        handleResetPasswordConfirm,
        isLoading,
        error: hookError,
        isSuccess,
    } = useResetPasswordConfirm();
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isPasswordFocused, setIsPasswordFocused] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);

    // Unwrap params
    const { uid, token } = React.use(params);

    const {
        register,
        handleSubmit,
        watch,
        formState: { errors, isValid },
    } = useForm<ResetPasswordConfirmFormData>({
        resolver: zodResolver(resetPasswordConfirmSchema),
        defaultValues: {
            new_password: "",
            re_new_password: "",
        },
        mode: "onChange",
    });

    const password = watch("new_password") || "";

    // Password checks
    const passwordChecks = PASSWORD_CHECKS.map((check) => ({
        ...check,
        passed: check.test(password),
    }));

    const showRules = isPasswordFocused && password.length > 0;
    const isPasswordValid = passwordChecks.every((check) => check.passed);

    const onSubmit = async (data: ResetPasswordConfirmFormData) => {
        setSubmitError(null);

        try {
            await handleResetPasswordConfirm({
                uid,
                token,
                new_password: data.new_password,
                re_new_password: data.re_new_password,
            });
        } catch (error: unknown) {
            setSubmitError(
                error?.data?.message ||
                    "Failed to reset password. Please try again.",
            );
        }
    };

    // Success state
    if (isSuccess) {
        return (
            <div className="flex min-h-[80vh] flex-col items-center justify-center px-4 py-12">
                <Card className="w-full max-w-md shadow-lg border-0 relative overflow-hidden">
                    <div className="absolute top-0 left-0 right-0 h-1 bg-linear-to-r from-green-400 to-emerald-500" />

                    <CardHeader className="text-center pb-2 pt-8">
                        <div className="mx-auto flex size-20 items-center justify-center rounded-full bg-green-50 dark:bg-green-900/20 mb-4 ring-4 ring-green-100 dark:ring-green-900/30">
                            <CheckCircle className="size-10 text-green-600 dark:text-green-400" />
                        </div>
                        <CardTitle className="text-2xl font-bold tracking-tight">
                            Password Reset Complete! 🎉
                        </CardTitle>
                        <CardDescription className="text-base">
                            Your password has been successfully updated.
                        </CardDescription>
                    </CardHeader>

                    <CardContent className="text-center pb-2">
                        <div className="space-y-2">
                            <p className="text-sm text-muted-foreground leading-relaxed">
                                You can now login with your new password.
                            </p>
                            <div className="mt-3 p-3 bg-muted/30 rounded-lg border border-border/50">
                                <p className="text-xs text-muted-foreground flex items-start gap-2">
                                    <Shield className="size-3 mt-0.5 shrink-0" />
                                    <span>
                                        For security reasons, we recommend
                                        logging out of all other devices.
                                    </span>
                                </p>
                            </div>
                        </div>
                    </CardContent>

                    <CardFooter className="flex flex-col gap-3 pt-4">
                        <Button
                            onClick={() => router.push("/signin")}
                            className="w-full h-11"
                        >
                            <ArrowLeft className="size-4 mr-2" />
                            Go to Login
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        );
    }

    // Main form
    return (
        <div className="flex min-h-[80vh] flex-col items-center justify-center px-4 py-12">
            <Card className="w-full max-w-md shadow-lg border-0 relative overflow-hidden">
                <CardHeader className="text-center space-y-2 pt-8">
                    <div className="mx-auto flex size-14 items-center justify-center rounded-full bg-primary/10 mb-2">
                        <Lock className="size-7 text-primary" />
                    </div>
                    <CardTitle className="text-2xl font-bold tracking-tight">
                        Create New Password
                    </CardTitle>
                    <CardDescription className="text-sm">
                        Enter your new password below.
                    </CardDescription>
                </CardHeader>

                <form onSubmit={handleSubmit(onSubmit)}>
                    <CardContent className="space-y-4">
                        {/* New Password */}
                        <div className="space-y-2">
                            <label
                                htmlFor="new_password"
                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                            >
                                New Password
                            </label>
                            <div className="relative">
                                <Input
                                    id="new_password"
                                    type={showPassword ? "text" : "password"}
                                    {...register("new_password")}
                                    placeholder="Enter new password"
                                    aria-invalid={!!errors.new_password}
                                    className={cn(
                                        "h-11 pl-4 pr-10 transition-all duration-200",
                                        errors.new_password &&
                                            "border-destructive focus-visible:ring-destructive",
                                        !errors.new_password &&
                                            isPasswordValid &&
                                            password.length > 0 &&
                                            "border-green-500 focus-visible:ring-green-500",
                                    )}
                                    onFocus={() => setIsPasswordFocused(true)}
                                    onBlur={() => setIsPasswordFocused(false)}
                                />
                                <button
                                    type="button"
                                    onClick={() =>
                                        setShowPassword(!showPassword)
                                    }
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                    aria-label={
                                        showPassword
                                            ? "Hide password"
                                            : "Show password"
                                    }
                                >
                                    {showPassword ? (
                                        <Eye size={16} />
                                    ) : (
                                        <EyeOff size={16} />
                                    )}
                                </button>
                            </div>

                            {/* Password strength indicators */}
                            {showRules && (
                                <div
                                    className="mt-2 space-y-1 text-sm"
                                    role="list"
                                >
                                    {passwordChecks.map((check) => (
                                        <div
                                            key={check.id}
                                            className="flex items-center gap-2"
                                            role="listitem"
                                        >
                                            <span
                                                className={cn(
                                                    "transition-colors",
                                                    check.passed
                                                        ? "text-green-500"
                                                        : "text-muted-foreground",
                                                )}
                                            >
                                                {check.passed ? "✓" : "○"}
                                            </span>
                                            <span
                                                className={cn(
                                                    "transition-colors",
                                                    check.passed
                                                        ? "text-green-500"
                                                        : "text-muted-foreground",
                                                )}
                                            >
                                                {check.label}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {errors.new_password && (
                                <p
                                    className="text-sm text-destructive flex items-center gap-1.5"
                                    role="alert"
                                >
                                    <AlertCircle className="size-4" />
                                    {errors.new_password.message}
                                </p>
                            )}
                        </div>

                        {/* Confirm Password */}
                        <div className="space-y-2">
                            <label
                                htmlFor="re_new_password"
                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                            >
                                Confirm Password
                            </label>
                            <div className="relative">
                                <Input
                                    id="re_new_password"
                                    type={
                                        showConfirmPassword
                                            ? "text"
                                            : "password"
                                    }
                                    {...register("re_new_password")}
                                    placeholder="Confirm your password"
                                    aria-invalid={!!errors.re_new_password}
                                    className={cn(
                                        "h-11 pl-4 pr-10 transition-all duration-200",
                                        errors.re_new_password &&
                                            "border-destructive focus-visible:ring-destructive",
                                        !errors.re_new_password &&
                                            watch("re_new_password") &&
                                            watch("new_password") ===
                                                watch("re_new_password") &&
                                            "border-green-500 focus-visible:ring-green-500",
                                    )}
                                />
                                <button
                                    type="button"
                                    onClick={() =>
                                        setShowConfirmPassword(
                                            !showConfirmPassword,
                                        )
                                    }
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                    aria-label={
                                        showConfirmPassword
                                            ? "Hide password"
                                            : "Show password"
                                    }
                                >
                                    {showConfirmPassword ? (
                                        <Eye size={16} />
                                    ) : (
                                        <EyeOff size={16} />
                                    )}
                                </button>
                            </div>
                            {errors.re_new_password && (
                                <p
                                    className="text-sm text-destructive flex items-center gap-1.5"
                                    role="alert"
                                >
                                    <AlertCircle className="size-4" />
                                    {errors.re_new_password.message}
                                </p>
                            )}
                            {!errors.re_new_password &&
                                watch("re_new_password") &&
                                watch("new_password") ===
                                    watch("re_new_password") && (
                                    <p className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1.5">
                                        <CheckCircle className="size-4" />
                                        Passwords match
                                    </p>
                                )}
                        </div>

                        {/* Error */}
                        {(submitError || hookError) && (
                            <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 animate-in fade-in-0 slide-in-from-top-1">
                                <p
                                    className="text-sm text-destructive flex items-start gap-2"
                                    role="alert"
                                >
                                    <XCircle className="size-4 mt-0.5 shrink-0" />
                                    <span>{submitError || hookError}</span>
                                </p>
                            </div>
                        )}

                        {/* Security Notice */}
                        <div className="rounded-lg bg-muted/30 border border-border/50 p-3">
                            <p className="text-xs text-muted-foreground flex items-start gap-2">
                                <KeyRound className="size-3 mt-0.5 shrink-0" />
                                <span>
                                    Your new password must be at least 8
                                    characters and include uppercase, lowercase,
                                    number, and symbol.
                                </span>
                            </p>
                        </div>
                    </CardContent>

                    <CardFooter className="flex flex-col gap-3 pt-2">
                        <Button
                            type="submit"
                            className="w-full h-11"
                            disabled={isLoading || !isValid || !isPasswordValid}
                        >
                            {isLoading ? (
                                <>
                                    <Spinner
                                        className="shrink-0 mr-2"
                                        aria-hidden
                                    />
                                    Resetting Password...
                                </>
                            ) : (
                                <>
                                    <Lock className="size-4 mr-2" />
                                    Reset Password
                                </>
                            )}
                        </Button>

                        <div className="flex items-center gap-4 w-full">
                            <div className="flex-1 h-px bg-border" />
                            <span className="text-xs text-muted-foreground shrink-0">
                                or
                            </span>
                            <div className="flex-1 h-px bg-border" />
                        </div>

                        <Button
                            variant="ghost"
                            onClick={() => router.push("/signin")}
                            className="w-full h-10 text-muted-foreground hover:text-foreground"
                        >
                            <ArrowLeft className="size-4 mr-2" />
                            Back to Login
                        </Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}
