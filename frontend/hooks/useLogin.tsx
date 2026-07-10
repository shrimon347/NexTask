// hooks/useLogin.ts
"use client";

import { useLoginMutation } from "@/redux/features/authApiSlice";
import { setAuth } from "@/redux/features/authSlice";
import { useAppDispatch } from "@/redux/hooks";
import { CheckCircle, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { toast } from "sonner";

interface LoginData {
    email: string;
    password: string;
}

export function useLogin() {
    const router = useRouter();
    const dispatch = useAppDispatch();
    const [login, { isLoading }] = useLoginMutation();
    const [submitError, setSubmitError] = useState<string | null>(null);

    const handleLogin = useCallback(
        async (data: LoginData) => {
            setSubmitError(null);

            try {
                await login({
                    email: data.email.trim().toLowerCase(),
                    password: data.password,
                }).unwrap();

                dispatch(setAuth());
                toast.success("Welcome back!", {
                    description: "You have been successfully logged in.",
                    icon: <CheckCircle className="text-green-500 size-5" />,
                });
                router.push("/dashboard");
            } catch (error: unknown) {
                console.log(error)
                const errorMessage =
                    error?.data?.message ||
                    error?.data?.errors?.detail ||
                    "Login failed. Please try again.";

                setSubmitError(errorMessage);
                toast.error("Login failed", {
                    description: errorMessage,
                    icon: <XCircle className="text-red-500 size-5" />,
                });
            }
        },
        [login, dispatch, router],
    );

    return {
        handleLogin,
        isLoading,
        submitError,
        setSubmitError,
    };
}
