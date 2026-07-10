// hooks/useResetPasswordConfirm.ts
"use client";

import { useResetPasswordConfirmMutation } from "@/redux/features/authApiSlice";
import { CheckCircle, XCircle } from "lucide-react";
import { useCallback, useState } from "react";
import { toast } from "sonner";

interface ResetPasswordConfirmData {
    uid: string;
    token: string;
    new_password: string;
    re_new_password: string;
}

interface ResetPasswordConfirmResponse {
    success: boolean;
    message: string;
}

export function useResetPasswordConfirm() {
    const [resetPasswordConfirm, { isLoading }] =
        useResetPasswordConfirmMutation();
    const [error, setError] = useState<string | null>(null);
    const [isSuccess, setIsSuccess] = useState(false);

    const handleResetPasswordConfirm = useCallback(
        async (
            data: ResetPasswordConfirmData,
        ): Promise<ResetPasswordConfirmResponse | undefined> => {
            setError(null);
            setIsSuccess(false);

            try {
                const response = await resetPasswordConfirm(data).unwrap();

                setIsSuccess(true);
                toast.success("Password reset successfully!", {
                    description:
                        "Your password has been updated. You can now login with your new password.",
                    icon: <CheckCircle className="text-green-500 size-5" />,
                    duration: 5000,
                });

                return response;
            } catch (error: unknown) {
                const errorMessage =
                    error?.data?.message ||
                    error?.data?.error ||
                    "Failed to reset password. The link may be invalid or expired.";

                setError(errorMessage);
                toast.error("Password reset failed", {
                    description: errorMessage,
                    icon: <XCircle className="text-red-500 size-5" />,
                    duration: 5000,
                });

                throw error;
            }
        },
        [resetPasswordConfirm],
    );

    return {
        handleResetPasswordConfirm,
        isLoading,
        error,
        isSuccess,
        setIsSuccess,
        setError,
    };
}
