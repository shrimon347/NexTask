"use client";

import { useLogoutMutation } from "@/redux/features/authApiSlice";
import { logout } from "@/redux/features/authSlice";
import { useAppDispatch } from "@/redux/hooks";
import { LogOut, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { toast } from "sonner";

export function useLogout() {
    const router = useRouter();
    const dispatch = useAppDispatch();
    const [logoutUser, { isLoading }] = useLogoutMutation();
    const [error, setError] = useState<string | null>(null);

    const handleLogout = useCallback(async () => {
        setError(null);

        try {
            await logoutUser().unwrap();

            dispatch(logout());
            toast.success("Logged out successfully!", {
                description: "You have been logged out of your account.",
                icon: <LogOut className="text-blue-500 size-5" />,
            });
            router.push("/signin");
        } catch (error: unknown) {
            console.error("Logout error:", error);
            const errorMessage =
                error?.data?.message ||
                error?.data?.error ||
                "Failed to logout. Please try again.";

            setError(errorMessage);
            toast.error("Logout failed", {
                description: errorMessage,
                icon: <XCircle className="text-red-500 size-5" />,
            });
        }
    }, [logoutUser, dispatch, router]);

    return {
        handleLogout,
        isLoading,
        error,
        setError,
    };
}
