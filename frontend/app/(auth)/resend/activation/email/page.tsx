/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/incompatible-library */
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
    ArrowLeft,
    CheckCircle,
    Mail,
    Send,
    Shield,
    XCircle,
} from "lucide-react";
import { useRouter } from "next/navigation";
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

// Import your existing hook
import { useResendActivation } from "@/hooks/useResendActivation";

const resendSchema = z.object({
    email: z
        .string()
        .min(1, "Email is required")
        .email("Please enter a valid email address"),
});

type ResendFormData = z.infer<typeof resendSchema>;

export default function ResendVerificationPage() {
    const router = useRouter();
    const {
        handleResendActivation,
        isLoading,
        error: hookError,
        isSuccess,
        setIsSuccess,
    } = useResendActivation();
    const [submitError, setSubmitError] = useState<string | null>(null);

    const {
        register,
        handleSubmit,
        watch,
        reset,
        formState: { errors, isValid, isDirty },
    } = useForm<ResendFormData>({
        resolver: zodResolver(resendSchema),
        defaultValues: {
            email: "",
        },
        mode: "onChange",
    });

    const emailValue = watch("email");

    const onSubmit = async (data: ResendFormData) => {
        setSubmitError(null);

        try {
            await handleResendActivation({ email: data.email });
            // Success is handled by the hook (toast + isSuccess state)
        } catch (error: unknown) {
            // Don't show specific error about email existence
            // Just show a generic message
            setSubmitError(null); // Don't show error to prevent email enumeration
        }
    };

    // Success state - Always show this regardless of whether email exists
    // This prevents email enumeration attacks
    if (isSuccess) {
        return (
            <div className="flex min-h-[80vh] flex-col items-center justify-center px-4 py-12">
                <Card className="w-full max-w-md shadow-lg border-0 relative overflow-hidden">
                    {/* Decorative gradient bar */}
                    <div className="absolute top-0 left-0 right-0 h-1 bg-linear-to-r from-green-400 to-emerald-500" />

                    <CardHeader className="text-center pb-2 pt-8">
                        <div className="mx-auto flex size-20 items-center justify-center rounded-full bg-green-50 dark:bg-green-900/20 mb-4 ring-4 ring-green-100 dark:ring-green-900/30">
                            <Mail className="size-10 text-green-600 dark:text-green-400" />
                        </div>
                        <CardTitle className="text-2xl font-bold tracking-tight">
                            Check Your Inbox
                        </CardTitle>
                        <CardDescription className="text-base">
                            If an account exists with this email, we&apos;ve
                            sent a verification link to:
                        </CardDescription>
                    </CardHeader>

                    <CardContent className="text-center pb-2">
                        <div className="bg-muted/50 px-4 py-3 rounded-lg inline-block border border-border/50">
                            <p className="text-sm font-medium text-foreground">
                                {emailValue}
                            </p>
                        </div>
                        <div className="mt-4 space-y-2">
                            <p className="text-sm text-muted-foreground leading-relaxed">
                                Please check your inbox and spam folder.
                            </p>
                            <p className="text-xs text-muted-foreground">
                                The verification link will expire in{" "}
                                <span className="font-medium text-foreground">
                                    24 hours
                                </span>
                                .
                            </p>
                        </div>
                    </CardContent>

                    <CardFooter className="flex flex-col gap-3 pt-4">
                        <Button
                            onClick={() => router.push("/signin")}
                            className="w-full h-11"
                        >
                            Go to Login
                        </Button>
                        <Button
                            variant="ghost"
                            onClick={() => {
                                setIsSuccess(false);
                                setSubmitError(null);
                                reset();
                            }}
                            className="w-full text-muted-foreground hover:text-foreground"
                        >
                            <ArrowLeft className="size-4 mr-2" />
                            Send again with different email
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
                        <Shield className="size-7 text-primary" />
                    </div>
                    <CardTitle className="text-2xl font-bold tracking-tight">
                        Resend Verification
                    </CardTitle>
                    <CardDescription className="text-sm">
                        Enter your email address to receive a new verification
                        link.
                    </CardDescription>
                </CardHeader>

                <form onSubmit={handleSubmit(onSubmit)}>
                    <CardContent className="space-y-4">
                        {/* Email Input */}
                        <div className="space-y-2">
                            <label
                                htmlFor="email"
                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                            >
                                Email Address
                            </label>
                            <div className="relative">
                                <Input
                                    id="email"
                                    type="email"
                                    {...register("email")}
                                    placeholder="m@example.com"
                                    aria-invalid={!!errors.email}
                                    className={cn(
                                        "h-11 pl-4 pr-10 transition-all duration-200",
                                        errors.email &&
                                            "border-destructive focus-visible:ring-destructive",
                                        !errors.email &&
                                            isDirty &&
                                            "border-green-500 focus-visible:ring-green-500",
                                    )}
                                />
                                {!errors.email && isDirty && (
                                    <CheckCircle className="absolute right-3 top-1/2 -translate-y-1/2 size-5 text-green-500 animate-in fade-in-0 zoom-in-50" />
                                )}
                                {errors.email && (
                                    <XCircle className="absolute right-3 top-1/2 -translate-y-1/2 size-5 text-destructive animate-in fade-in-0 zoom-in-50" />
                                )}
                            </div>

                            {/* Email validation feedback - only format validation, not existence */}
                            {errors.email ? (
                                <p
                                    className="text-sm text-destructive flex items-center gap-1.5"
                                    role="alert"
                                >
                                    <XCircle className="size-4" />
                                    {errors.email.message}
                                </p>
                            ) : isDirty && !errors.email ? (
                                <p className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1.5">
                                    <CheckCircle className="size-4" />
                                    Valid email format
                                </p>
                            ) : (
                                <p className="text-xs text-muted-foreground">
                                    We&apos;ll send a verification link if this
                                    email is registered.
                                </p>
                            )}
                        </div>

                        {/* Security Notice */}
                        <div className="rounded-lg bg-muted/30 border border-border/50 p-3 mb-5">
                            <p className="text-xs text-muted-foreground flex items-start gap-2">
                                <Shield className="size-3 mt-0.5 shrink-0" />
                                <span>
                                    For security reasons, we&apos;ll only send a
                                    verification email if this address is
                                    registered with us. You&apos;ll receive a
                                    confirmation message regardless of whether
                                    the email exists.
                                </span>
                            </p>
                        </div>

                        {/* Submit Error - Generic message only */}
                        {(submitError || hookError) && (
                            <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 animate-in fade-in-0 slide-in-from-top-1">
                                <p
                                    className="text-sm text-destructive flex items-start gap-2"
                                    role="alert"
                                >
                                    <XCircle className="size-4 mt-0.5 shrink-0" />
                                    <span>
                                        Something went wrong. Please try again
                                        later.
                                    </span>
                                </p>
                            </div>
                        )}
                    </CardContent>

                    <CardFooter className="flex flex-col gap-3 pt-2">
                        {/* Submit Button */}
                        <Button
                            type="submit"
                            className="w-full h-11"
                            disabled={isLoading || !isValid}
                        >
                            {isLoading ? (
                                <>
                                    <Spinner
                                        className="shrink-0 mr-2"
                                        aria-hidden
                                    />
                                    Sending...
                                </>
                            ) : (
                                <>
                                    <Send className="size-4 mr-2" />
                                    Send Verification Email
                                </>
                            )}
                        </Button>

                        {/* Divider */}
                        <div className="flex items-center gap-4 w-full">
                            <div className="flex-1 h-px bg-border" />
                            <span className="text-xs text-muted-foreground shrink-0">
                                or
                            </span>
                            <div className="flex-1 h-px bg-border" />
                        </div>

                        {/* Secondary Actions */}
                        <div className="flex flex-col sm:flex-row gap-2 w-full">
                            <Button
                                variant="outline"
                                onClick={() => router.push("/signin")}
                                className="flex-1 h-10"
                            >
                                <ArrowLeft className="size-4 mr-2" />
                                Back to Login
                            </Button>
                            <Button
                                variant="ghost"
                                onClick={() => router.push("/signup")}
                                className="flex-1 h-10 text-muted-foreground hover:text-foreground"
                            >
                                Create Account
                            </Button>
                        </div>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}
