"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
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
import { loginSchema } from "@/redux/schemas/auth.schema";

// Import hook
import { useLogin } from "@/hooks/useLogin";

// Import social login section
import { SocialLoginSection } from "./SocialLoginSection";

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm({
    className,
    ...props
}: React.ComponentProps<"form">) {
    const [showPassword, setShowPassword] = useState(false);
    const { handleLogin, isLoading, submitError } = useLogin();

    const {
        register,
        handleSubmit,
        formState: { errors, isValid },
    } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema),
        defaultValues: {
            email: "",
            password: "",
        },
        mode: "onChange",
    });

    const onSubmit = async (data: LoginFormData) => {
        await handleLogin({
            email: data.email,
            password: data.password,
        });
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
                    <h1 className="text-2xl font-bold">
                        Login to your account
                    </h1>
                    <p className="text-sm text-balance text-muted-foreground">
                        Enter your email below to login to your account
                    </p>
                </div>

                {/* EMAIL */}
                <Field>
                    <FieldLabel htmlFor="email">Email</FieldLabel>
                    <Input
                        id="email"
                        type="email"
                        placeholder="m@example.com"
                        {...register("email")}
                        aria-invalid={!!errors.email}
                    />
                    {errors.email && (
                        <p className="text-sm text-destructive" role="alert">
                            {errors.email.message}
                        </p>
                    )}
                </Field>

                {/* PASSWORD */}
                <Field>
                    <div className="flex items-center">
                        <FieldLabel htmlFor="password">Password</FieldLabel>
                        <Link
                            href="/password-reset"
                            className="ml-auto text-sm underline-offset-4 hover:underline text-muted-foreground hover:text-foreground transition-colors"
                        >
                            Forgot your password?
                        </Link>
                    </div>
                    <div className="relative">
                        <Input
                            id="password"
                            type={showPassword ? "text" : "password"}
                            className="pr-10"
                            {...register("password")}
                            aria-invalid={!!errors.password}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword((prev) => !prev)}
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
                    {errors.password && (
                        <p className="text-sm text-destructive" role="alert">
                            {errors.password.message}
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
                        {isLoading ? "Signing in..." : "Login"}
                    </Button>
                    {submitError && (
                        <p
                            className="mt-2 whitespace-pre-line text-sm text-destructive"
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
