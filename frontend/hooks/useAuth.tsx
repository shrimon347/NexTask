"use client";

import { useRetrieveUserQuery } from "@/redux/features/authApiSlice";
import { useAppSelector } from "@/redux/hooks";
import { useLogout } from "./useLogout";

export function useAuth() {
    const { data, isLoading, isFetching, error, refetch } =
        useRetrieveUserQuery();
    const isAuthenticated = useAppSelector(
        (state) => state.auth.isAuthenticated,
    );

    const {
        handleLogout,
        isLoading: isLoggingOut,
        error: logoutError,
    } = useLogout();

    return {
        // User data
        data,
        isLoading,
        isFetching,
        error,
        refetch,

        // Auth state
        isAuthenticated,
        isLoggedIn: isAuthenticated && !!data,

        // Logout
        logout: handleLogout,
        isLoggingOut,
        logoutError,
    };
}
