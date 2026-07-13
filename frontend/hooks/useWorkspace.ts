// hooks/useWorkspace.ts
/* eslint-disable @typescript-eslint/no-explicit-any */

import {
    clearSelectedWorkspace,
    setSelectedWorkspace,
} from "@/redux/features/workspaceSlice";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import {
    useCreateWorkspaceMutation,
    useDeleteWorkspaceMutation,
    useGetWorkspacesQuery,
} from "@/redux/services/workspaceApiSlice";
import { RootState } from "@/redux/store";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo } from "react";

// Define types - matching your API response
interface Workspace {
    id: string;
    name: string;
    description?: string;
    color?: string;
    owner_id: string;
    owner_email: string;
    owner_name: string;
    role: string;
    member_count: number;
    created_at: string;
    updated_at: string;
}

interface CreateWorkspaceData {
    name: string;
    description?: string;
    color?: string;
}

export const useWorkspace = () => {
    const dispatch = useAppDispatch();
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();

    const selectedWorkspace = useAppSelector(
        (state: RootState) => state.workspace.selectedWorkspace,
    );

    const { data, isLoading, error } = useGetWorkspacesQuery(undefined, {
        refetchOnFocus: false,
        keepUnusedDataFor: 3600,
    });

    // Extract workspaces from the response
    const workspaces = useMemo(() => {
        if (!data) return [];

        // If data is already an array (if base apiSlice already extracted)
        if (Array.isArray(data)) {
            return data;
        }

        // If data has a data property that's an array (your API response)
        if (
            typeof data === "object" &&
            "data" in data &&
            Array.isArray((data as any).data)
        ) {
            return (data as any).data;
        }

        return [];
    }, [data]);

    const [createWorkspaceMutation, { isLoading: isCreating }] =
        useCreateWorkspaceMutation();
    const [deleteWorkspaceMutation, { isLoading: isDeleting }] =
        useDeleteWorkspaceMutation();

    // Restore selection from URL on load
    useEffect(() => {
        if (workspaces.length === 0) return;

        const workspaceId = searchParams.get("workspaceId");

        if (workspaceId) {
            const workspace = workspaces.find((w) => w.id === workspaceId);
            if (workspace) {
                dispatch(setSelectedWorkspace(workspace));
                return;
            }
        }

        // If selected workspace doesn't exist anymore, clear it
        if (selectedWorkspace) {
            const stillExists = workspaces.some(
                (w) => w.id === selectedWorkspace.id,
            );
            if (!stillExists) {
                dispatch(clearSelectedWorkspace());
            }
        }
    }, [workspaces, searchParams, selectedWorkspace, dispatch]);

    const selectWorkspace = (workspace: Workspace) => {
        dispatch(setSelectedWorkspace(workspace));

        const isOnWorkspacePage = pathname?.includes("/workspace") || false;
        if (isOnWorkspacePage) {
            router.push(`/workspaces/${workspace.id}`);
        } else {
            const params = new URLSearchParams(searchParams?.toString() || "");
            params.set("workspaceId", workspace.id);
            router.push(`${pathname}?${params.toString()}`);
        }
    };

    const clearWorkspaceSelection = () => {
        dispatch(clearSelectedWorkspace());
        const params = new URLSearchParams(searchParams?.toString() || "");
        params.delete("workspaceId");
        router.push(`${pathname}?${params.toString()}`);
    };

    const createWorkspace = async (data: CreateWorkspaceData) => {
        try {
            const result = await createWorkspaceMutation(data).unwrap();

            // Handle the response - your API might return { data: { id: "...", ... } }
            let newWorkspace = result;

            // If result has a data property (nested response from create)
            if (
                result &&
                typeof result === "object" &&
                "data" in result &&
                result.data
            ) {
                newWorkspace = (result as any).data;
            }

            // Log to debug
            console.log("Created workspace:", newWorkspace);

            // Make sure we have an id
            if (!newWorkspace?.id) {
                console.error("No workspace ID in response:", result);
                throw new Error("Failed to get workspace ID from response");
            }

            dispatch(setSelectedWorkspace(newWorkspace));
            router.push(`/workspaces/${newWorkspace.id}`);
            return newWorkspace;
        } catch (error) {
            console.error("Failed to create workspace:", error);
            throw error;
        }
    };

    const deleteWorkspace = async (id: string) => {
        try {
            await deleteWorkspaceMutation(id).unwrap();
            if (selectedWorkspace?.id === id) {
                clearWorkspaceSelection();
            }
        } catch (error) {
            console.error("Failed to delete workspace:", error);
            throw error;
        }
    };

    return {
        workspaces,
        selectedWorkspace,
        isLoading,
        isCreating,
        isDeleting,
        error,
        selectWorkspace,
        clearWorkspaceSelection,
        createWorkspace,
        deleteWorkspace,
    };
};
