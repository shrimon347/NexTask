"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
    Field,
    FieldDescription,
    FieldGroup,
    FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

// Import schema

// Import hook
import { useRegister } from "@/hooks/useRegister";
import { registerSchema } from "@/redux/schemas/auth.schema";
import { SocialLoginSection } from "./SocialLoginSection";

type FormData = z.infer<typeof registerSchema>;

// Password checks configuration
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

export function SignupForm({
    className,
    ...props
}: React.ComponentProps<"form">) {
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isPasswordFocused, setIsPasswordFocused] = useState(false);

    const { handleRegister, isLoading, submitError } = useRegister();

    const {
        register,
        handleSubmit,
        control,
        reset,
        formState: { errors, isValid },
    } = useForm<FormData>({
        resolver: zodResolver(registerSchema),
        mode: "onChange",
    });

    const password = useWatch({ control, name: "password" }) || "";

    const passwordChecks = useMemo(
        () =>
            PASSWORD_CHECKS.map((check) => ({
                ...check,
                passed: check.test(password),
            })),
        [password],
    );

    const showRules = isPasswordFocused && password.length > 0;

    const onSubmit = async (data: FormData) => {
        await handleRegister({
            name: data.name,
            email: data.email,
            password: data.password,
            re_password: data.confirm_password,
        });
        reset();
    };

    return (
        <form
            onSubmit={handleSubmit(onSubmit)}
            className={cn("flex flex-col gap-6", className)}
            {...props}
        >
            <FieldGroup>
                {/* HEADER */}
                <div className="flex flex-col items-center gap-1 text-center">
                    <h1 className="text-2xl font-bold">Create your account</h1>
                    <p className="text-sm text-muted-foreground">
                        Fill in the form below to create your account
                    </p>
                </div>

                {/* NAME */}
                <Field>
                    <FieldLabel htmlFor="name">Full Name</FieldLabel>
                    <Input
                        id="name"
                        {...register("name")}
                        placeholder="John Doe"
                        aria-invalid={!!errors.name}
                    />
                    {errors.name && (
                        <p className="text-destructive text-sm" role="alert">
                            {errors.name.message}
                        </p>
                    )}
                </Field>

                {/* EMAIL */}
                <Field>
                    <FieldLabel htmlFor="email">Email</FieldLabel>
                    <Input
                        id="email"
                        type="email"
                        {...register("email")}
                        placeholder="m@example.com"
                        aria-invalid={!!errors.email}
                    />
                    <FieldDescription>
                        We&apos;ll use this to contact you.
                    </FieldDescription>
                    {errors.email && (
                        <p className="text-destructive text-sm" role="alert">
                            {errors.email.message}
                        </p>
                    )}
                </Field>

                {/* PASSWORD */}
                <Field>
                    <FieldLabel htmlFor="password">Password</FieldLabel>
                    <div className="relative">
                        <Input
                            id="password"
                            type={showPassword ? "text" : "password"}
                            {...register("password")}
                            className={cn(
                                "pr-10",
                                errors.password && "border-destructive",
                            )}
                            onFocus={() => setIsPasswordFocused(true)}
                            onBlur={() => setIsPasswordFocused(false)}
                            aria-invalid={!!errors.password}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                            aria-label={
                                showPassword ? "Hide password" : "Show password"
                            }
                        >
                            {showPassword ? (
                                <Eye size={16} />
                            ) : (
                                <EyeOff size={16} />
                            )}
                        </button>
                    </div>

                    {showRules && (
                        <div className="mt-2 space-y-1 text-sm" role="list">
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

                    {errors.password && (
                        <p
                            className="text-destructive text-sm mt-1"
                            role="alert"
                        >
                            {errors.password.message}
                        </p>
                    )}
                </Field>

                {/* CONFIRM PASSWORD */}
                <Field>
                    <FieldLabel htmlFor="confirm_password">
                        Confirm Password
                    </FieldLabel>
                    <div className="relative">
                        <Input
                            id="confirm_password"
                            type={showConfirmPassword ? "text" : "password"}
                            {...register("confirm_password")}
                            className={cn(
                                "pr-10",
                                errors.confirm_password && "border-destructive",
                            )}
                            aria-invalid={!!errors.confirm_password}
                        />
                        <button
                            type="button"
                            onClick={() =>
                                setShowConfirmPassword(!showConfirmPassword)
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
                    {errors.confirm_password && (
                        <p className="text-destructive text-sm" role="alert">
                            {errors.confirm_password.message}
                        </p>
                    )}
                </Field>

                {/* SUBMIT */}
                <Field>
                    <Button
                        type="submit"
                        className="w-full"
                        disabled={isLoading || !isValid}
                    >
                        {isLoading && (
                            <Spinner className="shrink-0 mr-2" aria-hidden />
                        )}
                        {isLoading ? "Creating account..." : "Create Account"}
                    </Button>
                    {submitError && (
                        <p
                            className="text-destructive text-sm mt-2"
                            role="alert"
                        >
                            {submitError}
                        </p>
                    )}
                </Field>

                {/* SOCIAL LOGIN */}
                <SocialLoginSection />

                {/* FOOTER */}
                <Field>
                    <FieldDescription className="text-center">
                        Don&apos;t have an account?{" "}
                        <Link
                            href="/signup"
                            className="text-primary hover:underline font-medium"
                        >
                            Sign up
                        </Link>
                        <br />
                        <Link
                            href="/resend-verification"
                            className="text-muted-foreground hover:text-foreground hover:underline transition-colors"
                        >
                            Resend verification
                        </Link>
                    </FieldDescription>
                </Field>
            </FieldGroup>
        </form>
    );
}
