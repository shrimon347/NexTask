/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import { useResetPasswordMutation } from "@/redux/features/authApiSlice";
import { CheckCircle } from "lucide-react";
import { useCallback, useState } from "react";
import { toast } from "sonner";

interface ResetPasswordData {
    email: string;
}

interface ResetPasswordResponse {
    success: boolean;
    message: string;
}

export function useResetPassword() {
    const [resetPassword, { isLoading }] = useResetPasswordMutation();
    const [error, setError] = useState<string | null>(null);
    const [isSuccess, setIsSuccess] = useState(false);

    const handleResetPassword = useCallback(
        async (
            data: ResetPasswordData,
        ): Promise<ResetPasswordResponse | undefined> => {
            setError(null);
            setIsSuccess(false);

            try {
                const response = await resetPassword(data.email).unwrap();

                setIsSuccess(true);
                toast.success("Password reset email sent!", {
                    description:
                        "If an account exists with this email, you'll receive a password reset link.",
                    icon: <CheckCircle className="text-green-500 size-5" />,
                    duration: 5000,
                });

                return response;
            } catch (error: unknown) {
                // Always show a generic message to prevent email enumeration
                toast.success("Password reset email sent!", {
                    description:
                        "If an account exists with this email, you'll receive a password reset link.",
                    icon: <CheckCircle className="text-green-500 size-5" />,
                    duration: 5000,
                });

                setIsSuccess(true);
                setError("Unable to process request. Please try again later.");
            }
        },
        [resetPassword],
    );

    return {
        handleResetPassword,
        isLoading,
        error,
        isSuccess,
        setIsSuccess,
        setError,
    };
}
