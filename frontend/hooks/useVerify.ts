// hooks/useVerify.ts
"use client";

import { useVerifyMutation } from "@/redux/features/authApiSlice";
import { finishInitialLoad, logout, setAuth } from "@/redux/features/authSlice";
import { useAppDispatch } from "@/redux/hooks";
import { useEffect } from "react";

export default function useVerify() {
    const dispatch = useAppDispatch();
    const [verify] = useVerifyMutation();

    useEffect(() => {
        const verifyUser = async () => {
            try {
                const response = await verify(undefined).unwrap();

                // If verification succeeds, user is authenticated
                if (response?.user) {
                    dispatch(setAuth());
                } else {
                    // No user data, but verification succeeded
                    // Could still be authenticated
                    dispatch(setAuth());
                }
            } catch (error) {
                // Verification failed - user is not authenticated
                console.error("Verification failed:", error);
                dispatch(logout());
            } finally {
                // Always set loading to false
                dispatch(finishInitialLoad());
            }
        };

        verifyUser();
    }, [verify, dispatch]);
}
