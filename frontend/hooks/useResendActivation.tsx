/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import { useResendActivationMutation } from "@/redux/features/authApiSlice";
import { CheckCircle } from "lucide-react";
import { useCallback, useState } from "react";
import { toast } from "sonner";

interface ResendActivationData {
    email: string;
}

export function useResendActivation() {
    const [resendActivation, { isLoading }] = useResendActivationMutation();
    const [error, setError] = useState<string | null>(null);
    const [isSuccess, setIsSuccess] = useState(false);

    const handleResendActivation = useCallback(
        async (data: ResendActivationData) => {
            setError(null);
            setIsSuccess(false);

            try {
                await resendActivation(data).unwrap();

                setIsSuccess(true);
                // Always show success, even if email doesn't exist
                toast.success("Verification email sent!", {
                    description:
                        "If an account exists with this email, you'll receive a verification link.",
                    icon: <CheckCircle className="text-green-500 size-5" />,
                    duration: 5000,
                });
            } catch (error: unknown) {
                // Don't expose whether the email exists or not
                // Always show a generic success message to prevent email enumeration
                setIsSuccess(true);
                toast.success("Verification email sent!", {
                    description:
                        "If an account exists with this email, you'll receive a verification link.",
                    icon: <CheckCircle className="text-green-500 size-5" />,
                    duration: 5000,
                });

                // Set a generic error for internal use
                setError("Unable to process request. Please try again later.");
            }
        },
        [resendActivation],
    );

    return {
        handleResendActivation,
        isLoading,
        error,
        isSuccess,
        setError,
        setIsSuccess,
    };
}
