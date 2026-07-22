// hooks/useProject.ts
/* eslint-disable @typescript-eslint/no-explicit-any */
import type {
    AddProjectMemberData,
    BulkAddMembersData,
    CreateProjectData,
    ProjectListQueryParams,
    UpdateProgressData,
    UpdateProjectData,
    UpdateStatusData,
} from "@/redux/services/projectApiSlice";
import {
    useAddProjectMemberMutation,
    useArchiveProjectMutation,
    useBulkAddProjectMembersMutation,
    useCreateProjectMutation,
    useDeleteProjectMutation,
    useGetProjectQuery,
    useGetProjectsQuery,
    useRemoveProjectMemberMutation,
    useUpdateMemberRoleMutation,
    useUpdateMemberTagsMutation,
    useUpdateProjectMutation,
    useUpdateProjectProgressMutation,
    useUpdateProjectStatusMutation,
} from "@/redux/services/projectApiSlice";
import { useRouter } from "next/navigation";
import { useCallback, useMemo, useState } from "react";
import { toast } from "sonner";

// =============================================================================
// Types
// =============================================================================

interface UseProjectsOptions {
    workspaceId?: string;
    autoFetch?: boolean;
    queryParams?: Partial<Omit<ProjectListQueryParams, "workspaceId">>;
}

// =============================================================================
// Constants
// =============================================================================

const QUERY_OPTIONS = {
    refetchOnFocus: false,
    refetchOnMountOrArgChange: false,
    keepUnusedDataFor: 300, // 5 minutes
} as const;

// =============================================================================
// Hook
// =============================================================================

export const useProjects = (options: UseProjectsOptions = {}) => {
    const { workspaceId, autoFetch = true, queryParams = {} } = options;
    const router = useRouter();

    // ============ State ============
    const [currentProjectId, setCurrentProjectId] = useState<string | null>(
        null,
    );

    // ============ Queries ============

    const projectsQuery = useGetProjectsQuery(
        {
            workspaceId: workspaceId || "",
            ...queryParams,
        } as ProjectListQueryParams,
        { skip: !workspaceId || !autoFetch, ...QUERY_OPTIONS },
    );

    const projectDetailQuery = useGetProjectQuery(currentProjectId || "", {
        skip: !currentProjectId || !autoFetch,
        ...QUERY_OPTIONS,
    });

    // ============ Mutations ============

    const [createProjectMutation, { isLoading: isCreating }] =
        useCreateProjectMutation();
    const [updateProjectMutation, { isLoading: isUpdating }] =
        useUpdateProjectMutation();
    const [deleteProjectMutation, { isLoading: isDeleting }] =
        useDeleteProjectMutation();
    const [updateStatusMutation, { isLoading: isUpdatingStatus }] =
        useUpdateProjectStatusMutation();
    const [updateProgressMutation, { isLoading: isUpdatingProgress }] =
        useUpdateProjectProgressMutation();
    const [archiveProjectMutation, { isLoading: isArchiving }] =
        useArchiveProjectMutation();
    const [addMemberMutation, { isLoading: isAddingMember }] =
        useAddProjectMemberMutation();
    const [bulkAddMembersMutation, { isLoading: isBulkAddingMembers }] =
        useBulkAddProjectMembersMutation();
    const [removeMemberMutation, { isLoading: isRemovingMember }] =
        useRemoveProjectMemberMutation();
    const [updateMemberRoleMutation, { isLoading: isUpdatingMemberRole }] =
        useUpdateMemberRoleMutation();
    const [updateMemberTagsMutation, { isLoading: isUpdatingMemberTags }] =
        useUpdateMemberTagsMutation();

    // ============ Generic Mutation Handler ============

    const handleMutation = useCallback(
        async <T>(
            mutation: (...args: any[]) => Promise<{ data?: T }>,
            successMessage: string,
            errorMessage: string,
        ): Promise<T> => {
            try {
                const result = await mutation().unwrap();
                toast.success(successMessage);
                return result;
            } catch (error: any) {
                const message = error?.data?.message || errorMessage;
                toast.error(message);
                throw error;
            }
        },
        [],
    );

    // ============ Actions ============

    const createProject = useCallback(
        (data: CreateProjectData) => {
            if (!workspaceId) {
                toast.error("No workspace selected");
                throw new Error("No workspace selected");
            }
            return handleMutation(
                () => createProjectMutation({ workspaceId, ...data }),
                "Project created successfully",
                "Failed to create project",
            );
        },
        [workspaceId, createProjectMutation, handleMutation],
    );

    const updateProject = useCallback(
        (projectId: string, data: UpdateProjectData) =>
            handleMutation(
                () => updateProjectMutation({ projectId, data }),
                "Project updated successfully",
                "Failed to update project",
            ),
        [updateProjectMutation, handleMutation],
    );

    const deleteProject = useCallback(
        async (projectId: string) => {
            await handleMutation(
                () => deleteProjectMutation(projectId),
                "Project deleted successfully",
                "Failed to delete project",
            );
            if (currentProjectId === projectId) {
                setCurrentProjectId(null);
            }
        },
        [deleteProjectMutation, currentProjectId, handleMutation],
    );
    
    const updateProjectStatus = useCallback(
        (projectId: string, status: UpdateStatusData) =>
            handleMutation(
                () => updateStatusMutation({ projectId, data: status }),
                "Project status updated",
                "Failed to update status",
            ),
        [updateStatusMutation, handleMutation],
    );

    const updateProjectProgress = useCallback(
        (projectId: string, progress: UpdateProgressData) =>
            handleMutation(
                () => updateProgressMutation({ projectId, data: progress }),
                "Project progress updated",
                "Failed to update progress",
            ),
        [updateProgressMutation, handleMutation],
    );

    const archiveProject = useCallback(
        (projectId: string, isArchived: boolean) =>
            handleMutation(
                () =>
                    archiveProjectMutation({
                        projectId,
                        data: { is_archived: isArchived },
                    }),
                isArchived ? "Project archived" : "Project unarchived",
                "Failed to archive project",
            ),
        [archiveProjectMutation, handleMutation],
    );

    const addProjectMember = useCallback(
        (projectId: string, data: AddProjectMemberData) =>
            handleMutation(
                () => addMemberMutation({ projectId, data }),
                "Member added to project",
                "Failed to add member",
            ),
        [addMemberMutation, handleMutation],
    );

    const bulkAddProjectMembers = useCallback(
        (projectId: string, data: BulkAddMembersData) =>
            handleMutation(
                () => bulkAddMembersMutation({ projectId, data }),
                `Members added: ${data.members.length} processed`,
                "Failed to add members",
            ),
        [bulkAddMembersMutation, handleMutation],
    );

    const removeProjectMember = useCallback(
        (projectId: string, userId: string) =>
            handleMutation(
                () =>
                    removeMemberMutation({
                        projectId,
                        data: { user_id: userId },
                    }),
                "Member removed from project",
                "Failed to remove member",
            ),
        [removeMemberMutation, handleMutation],
    );

    const updateMemberRole = useCallback(
        (projectId: string, userId: string, role: string) =>
            handleMutation(
                () =>
                    updateMemberRoleMutation({
                        projectId,
                        data: { user_id: userId, role } as any,
                    }),
                "Member role updated",
                "Failed to update role",
            ),
        [updateMemberRoleMutation, handleMutation],
    );

    const updateMemberTags = useCallback(
        (projectId: string, userId: string, tags: string[]) =>
            handleMutation(
                () =>
                    updateMemberTagsMutation({
                        projectId,
                        data: { user_id: userId, tags },
                    }),
                "Member tags updated",
                "Failed to update tags",
            ),
        [updateMemberTagsMutation, handleMutation],
    );

    const selectProject = useCallback(
        (projectId: string | null) => {
            setCurrentProjectId(projectId);
            if (projectId) {
                router.push(`/projects/${projectId}`);
            }
        },
        [router],
    );

    // ============ Computed Values ============

    const projects = useMemo(
        () => projectsQuery.data || [],
        [projectsQuery.data],
    );
    const currentProject = useMemo(
        () => projectDetailQuery.data || null,
        [projectDetailQuery.data],
    );
    const isLoading = projectsQuery.isLoading || projectDetailQuery.isLoading;
    const isFetching =
        projectsQuery.isFetching || projectDetailQuery.isFetching;

    // ============ Return ============

    return {
        // Data
        projects,
        currentProject,
        projectDetail: currentProject,
        currentProjectId,

        // Loading states
        isLoading,
        isFetching,
        isCreating,
        isUpdating,
        isDeleting,
        isUpdatingStatus,
        isUpdatingProgress,
        isArchiving,
        isAddingMember,
        isBulkAddingMembers,
        isRemovingMember,
        isUpdatingMemberRole,
        isUpdatingMemberTags,

        // Errors
        error: projectsQuery.error || projectDetailQuery.error,
        projectsError: projectsQuery.error,
        projectDetailError: projectDetailQuery.error,

        // Actions
        createProject,
        updateProject,
        deleteProject,
        updateProjectStatus,
        updateProjectProgress,
        archiveProject,
        addProjectMember,
        bulkAddProjectMembers,
        removeProjectMember,
        updateMemberRole,
        updateMemberTags,
        selectProject,
        setCurrentProjectId,

        // Refetch
        refetchProjects: projectsQuery.refetch,
        refetchProjectDetail: projectDetailQuery.refetch,
    };
};
