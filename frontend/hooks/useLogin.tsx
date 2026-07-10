"use client";

import { useLoginMutation } from "@/redux/features/authApiSlice";
import { useAppSelector } from "@/redux/hooks";
import { CheckCircle, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

interface LoginData {
    email: string;
    password: string;
}

export function useLogin() {
    const router = useRouter();
    const [login, { isLoading }] = useLoginMutation();
    const accessToken = useAppSelector((state) => state.auth.accessToken);
    const [submitError, setSubmitError] = useState<string | null>(null);

    // Redirect if already logged in
    useEffect(() => {
        if (accessToken) {
            router.replace("/dashboard");
        }
    }, [accessToken, router]);

    const handleLogin = useCallback(
        async (data: LoginData) => {
            setSubmitError(null);

            try {
                const response = await login({
                    email: data.email.trim().toLowerCase(),
                    password: data.password,
                }).unwrap();

                if ("access" in response.data) {
                    toast.success("Welcome back!", {
                        description: "You have been successfully logged in.",
                        icon: <CheckCircle className="text-green-500 size-5" />,
                    });
                    router.replace("/dashboard");
                    return;
                }

                const errorMessage =
                    "Two-factor authentication is required for this account, but the 2FA login screen is not implemented yet.";

                setSubmitError(errorMessage);
                toast.error("2FA Required", {
                    description: errorMessage,
                    icon: <XCircle className="text-red-500 size-5" />,
                });
            } catch (error: unknown) {
                const errorMessage =
                    error?.data?.message ||
                    error?.data?.error ||
                    error?.message ||
                    "Login failed. Please try again.";

                setSubmitError(errorMessage);
                toast.error("Login failed", {
                    description: errorMessage,
                    icon: <XCircle className="text-red-500 size-5" />,
                });
            }
        },
        [login, router],
    );

    return {
        handleLogin,
        isLoading,
        submitError,
        setSubmitError,
    };
}
