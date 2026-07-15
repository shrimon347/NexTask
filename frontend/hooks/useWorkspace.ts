/* eslint-disable @typescript-eslint/no-explicit-any */

import {
    clearSelectedWorkspace,
    setSelectedWorkspace,
} from "@/redux/features/workspaceSlice";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import {
    useCreateWorkspaceMutation,
    useDeleteWorkspaceMutation,
    useGetWorkspaceQuery,
    useGetWorkspacesQuery,
    useUpdateWorkspaceMutation,
} from "@/redux/services/workspaceApiSlice";
import { RootState } from "@/redux/store";
import { skipToken } from "@reduxjs/toolkit/query";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo } from "react";

// Define types
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

interface WorkspaceDetail extends Workspace {
    owner: {
        id: string;
        email: string;
        name: string;
    };
    project_count: number;
    members: Array<{
        id: string;
        email: string;
        name: string;
        profile_picture: string;
        role: string;
        joined_at: string;
    }>;
}

interface CreateWorkspaceData {
    name: string;
    description?: string;
    color?: string;
}

type UpdateWorkspaceData = CreateWorkspaceData;

export const useWorkspace = (workspaceId?: string) => {
    const dispatch = useAppDispatch();
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();

    const selectedWorkspace = useAppSelector(
        (state: RootState) => state.workspace.selectedWorkspace,
    );

    // Resolve the active workspace ID from the caller or the URL.
    const currentWorkspaceId = workspaceId ?? searchParams.get("workspaceId");

    // Get all workspaces (list view)
    const {
        data,
        isLoading: isLoadingWorkspaces,
        error,
    } = useGetWorkspacesQuery(undefined, {
        refetchOnFocus: false,
        keepUnusedDataFor: 3600,
    });

    const {
        data: workspaceDetailData,
        isLoading: isLoadingWorkspaceDetail,
        error: workspaceDetailError,
        refetch: refetchWorkspaceDetail,
    } = useGetWorkspaceQuery(currentWorkspaceId ?? skipToken);

    // Extract workspaces from the response
    const workspaces = useMemo(() => {
        if (!data) return [];

        if (Array.isArray(data)) {
            return data;
        }

        if (
            typeof data === "object" &&
            "data" in data &&
            Array.isArray((data as any).data)
        ) {
            return (data as any).data;
        }

        return [];
    }, [data]);

    // Extract workspace detail from response
    const workspaceDetail = useMemo(() => {
        if (!workspaceDetailData) return null;

        // If response has data property
        if (
            typeof workspaceDetailData === "object" &&
            "data" in workspaceDetailData &&
            workspaceDetailData.data
        ) {
            return (workspaceDetailData as any).data as WorkspaceDetail;
        }

        return workspaceDetailData as WorkspaceDetail;
    }, [workspaceDetailData]);

    // Find selected workspace from the list or use detail
    const resolvedSelectedWorkspace = useMemo(() => {
        const isWorkspaceListPage = pathname === "/workspaces";

        if (isWorkspaceListPage && !currentWorkspaceId) {
            return null;
        }

        // If we have detail data, use it
        if (workspaceDetail) {
            return workspaceDetail;
        }

        // If we have a selected workspace in Redux, use it
        if (selectedWorkspace) {
            return selectedWorkspace;
        }

        // Try to find from workspaces list using current ID
        if (currentWorkspaceId && workspaces.length > 0) {
            return workspaces.find((w) => w.id === currentWorkspaceId) || null;
        }

        return null;
    }, [
        workspaceDetail,
        selectedWorkspace,
        workspaces,
        currentWorkspaceId,
        pathname,
    ]);

    const getWorkspaceRoute = (nextWorkspaceId?: string) =>
        nextWorkspaceId ? `/workspaces/${nextWorkspaceId}` : "/workspaces";

    const [createWorkspaceMutation, { isLoading: isCreating }] =
        useCreateWorkspaceMutation();
    const [deleteWorkspaceMutation, { isLoading: isDeleting }] =
        useDeleteWorkspaceMutation();
    const [updateWorkspaceMutation, { isLoading: isUpdating }] =
        useUpdateWorkspaceMutation();

    // Update Redux when workspace changes
    useEffect(() => {
        if (
            resolvedSelectedWorkspace &&
            resolvedSelectedWorkspace.id !== selectedWorkspace?.id
        ) {
            dispatch(setSelectedWorkspace(resolvedSelectedWorkspace));
        }
    }, [resolvedSelectedWorkspace, selectedWorkspace, dispatch]);

    useEffect(() => {
        if (
            pathname === "/workspaces" &&
            !currentWorkspaceId &&
            selectedWorkspace
        ) {
            dispatch(clearSelectedWorkspace());
        }
    }, [pathname, currentWorkspaceId, selectedWorkspace, dispatch]);

    const selectWorkspace = (workspace: Workspace) => {
        dispatch(setSelectedWorkspace(workspace));

        router.push(getWorkspaceRoute(workspace.id));
    };

    const clearWorkspaceSelection = () => {
        dispatch(clearSelectedWorkspace());

        router.push(getWorkspaceRoute());
    };

    const createWorkspace = async (data: CreateWorkspaceData) => {
        try {
            const result = await createWorkspaceMutation(data).unwrap();

            let newWorkspace = result;

            if (
                result &&
                typeof result === "object" &&
                "data" in result &&
                result.data
            ) {
                newWorkspace = (result as any).data;
            }

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

    const updateWorkspace = async (id: string, data: UpdateWorkspaceData) => {
        try {
            const result = await updateWorkspaceMutation({ id, data }).unwrap();

            const baseWorkspace =
                workspaceDetail ||
                selectedWorkspace ||
                workspaces.find((workspace) => workspace.id === id) ||
                null;

            const updatedWorkspace = {
                ...(baseWorkspace || {}),
                ...result,
                ...data,
                id,
            };

            dispatch(setSelectedWorkspace(updatedWorkspace as any));
            return updatedWorkspace;
        } catch (error) {
            console.error("Failed to update workspace:", error);
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
        // Data
        workspaces,
        selectedWorkspace: resolvedSelectedWorkspace,
        workspaceDetail,
        currentWorkspaceId,

        // Loading states
        isLoading: isLoadingWorkspaces || isLoadingWorkspaceDetail,
        isWorkspaceDetailLoading: isLoadingWorkspaceDetail,
        isCreating,
        isUpdating,
        isDeleting,

        // Errors
        error: error || workspaceDetailError,

        // Actions
        selectWorkspace,
        clearWorkspaceSelection,
        createWorkspace,
        updateWorkspace,
        deleteWorkspace,
        refetchWorkspaceDetail,
    };
};
