// redux/services/projectApiSlice.ts
import {
    AddProjectMemberData,
    ArchiveProjectData,
    BulkAddMembersData,
    BulkOperationResponse,
    CreateProjectData,
    ProjectDetail,
    ProjectListItem,
    ProjectListQueryParams,
    RemoveMemberData,
    UpdateMemberRoleData,
    UpdateMemberTagsData,
    UpdateProgressData,
    UpdateProjectData,
    UpdateStatusData,
} from "../schemas/projects.schema";
import { apiSlice } from "./apiSlice";

// ============ Types ============

interface ApiResponse<T> {
    success: boolean;
    message: string;
    data: T;
    errors: null | Record<string, string>;
    error_code: null | string;
    timestamp: string;
}

// ============ API Slice ============

export const projectApiSlice = apiSlice.injectEndpoints({
    endpoints: (builder) => ({
        // ============ QUERIES ============

        // Get all projects in a workspace
        getProjects: builder.query<ProjectListItem[], ProjectListQueryParams>({
            query: ({ workspaceId, ...params }) => ({
                url: `/workspaces/${workspaceId}/projects/`,
                method: "GET",
                params,
            }),
            transformResponse: (response: ApiResponse<ProjectListItem[]>) => {
                return response.data;
            },
            providesTags: (result) =>
                result
                    ? [
                          ...result.map(({ id }) => ({
                              type: "Project" as const,
                              id,
                          })),
                          { type: "Project", id: "LIST" },
                      ]
                    : [{ type: "Project", id: "LIST" }],
        }),

        // Get single project detail
        getProject: builder.query<ProjectDetail, string>({
            query: (projectId) => ({
                url: `/projects/${projectId}/`,
                method: "GET",
            }),
            transformResponse: (response: ApiResponse<ProjectDetail>) => {
                return response.data;
            },
            providesTags: (result, error, id) => [{ type: "Project", id }],
        }),

        // ============ MUTATIONS ============

        // Create project
        createProject: builder.mutation<
            ProjectDetail,
            { workspaceId: string; data: CreateProjectData }
        >({
            query: ({ workspaceId, data }) => ({
                url: `/workspaces/${workspaceId}/projects/`,
                method: "POST",
                body: data,
            }),
            transformResponse: (response: ApiResponse<ProjectDetail>) => {
                return response.data;
            },
            invalidatesTags: [{ type: "Project", id: "LIST" }],
        }),

        // Update project
        updateProject: builder.mutation<
            ProjectDetail,
            { projectId: string; data: UpdateProjectData }
        >({
            query: ({ projectId, data }) => ({
                url: `/projects/${projectId}/`,
                method: "PATCH",
                body: data,
            }),
            transformResponse: (response: ApiResponse<ProjectDetail>) => {
                return response.data;
            },
            invalidatesTags: (result, error, { projectId }) => [
                { type: "Project", id: projectId },
                { type: "Project", id: "LIST" },
            ],
        }),

        // Delete project
        deleteProject: builder.mutation<void, string>({
            query: (projectId) => ({
                url: `/projects/${projectId}/`,
                method: "DELETE",
            }),
            invalidatesTags: (result, error, id) => [
                { type: "Project", id },
                { type: "Project", id: "LIST" },
            ],
        }),

        // Add to your existing apiSlice
        getWorkspaceMembersForDropdown: builder.query<
            MemberDropdownItem[],
            { workspaceId: string }
        >({
            query: ({ workspaceId }) => ({
                url: `/workspaces/${workspaceId}/members/dropdown/`,
                method: "GET",
            }),
            transformResponse: (response: ApiResponse<MemberDropdownItem[]>) =>
                response.data,
        }),

        // ============ STATUS & PROGRESS ============

        // Update project status
        updateProjectStatus: builder.mutation<
            ProjectDetail,
            { projectId: string; data: UpdateStatusData }
        >({
            query: ({ projectId, data }) => ({
                url: `/projects/${projectId}/status/`,
                method: "PATCH",
                body: data,
            }),
            transformResponse: (response: ApiResponse<ProjectDetail>) => {
                return response.data;
            },
            invalidatesTags: (result, error, { projectId }) => [
                { type: "Project", id: projectId },
                { type: "Project", id: "LIST" },
            ],
        }),

        // Update project progress
        updateProjectProgress: builder.mutation<
            ProjectDetail,
            { projectId: string; data: UpdateProgressData }
        >({
            query: ({ projectId, data }) => ({
                url: `/projects/${projectId}/progress/`,
                method: "PATCH",
                body: data,
            }),
            transformResponse: (response: ApiResponse<ProjectDetail>) => {
                return response.data;
            },
            invalidatesTags: (result, error, { projectId }) => [
                { type: "Project", id: projectId },
                { type: "Project", id: "LIST" },
            ],
        }),

        // ============ ARCHIVE ============

        // Archive/unarchive project
        archiveProject: builder.mutation<
            ProjectDetail,
            { projectId: string; data: ArchiveProjectData }
        >({
            query: ({ projectId, data }) => ({
                url: `/projects/${projectId}/archive/`,
                method: "PATCH",
                body: data,
            }),
            transformResponse: (response: ApiResponse<ProjectDetail>) => {
                return response.data;
            },
            invalidatesTags: (result, error, { projectId }) => [
                { type: "Project", id: projectId },
                { type: "Project", id: "LIST" },
            ],
        }),

        // ============ MEMBERS ============

        // Add single member to project
        addProjectMember: builder.mutation<
            ProjectDetail,
            { projectId: string; data: AddProjectMemberData }
        >({
            query: ({ projectId, data }) => ({
                url: `/projects/${projectId}/members/add/`,
                method: "POST",
                body: data,
            }),
            transformResponse: (response: ApiResponse<ProjectDetail>) => {
                return response.data;
            },
            invalidatesTags: (result, error, { projectId }) => [
                { type: "Project", id: projectId },
                { type: "Project", id: "LIST" },
            ],
        }),

        // Bulk add members to project
        bulkAddProjectMembers: builder.mutation<
            BulkOperationResponse,
            { projectId: string; data: BulkAddMembersData }
        >({
            query: ({ projectId, data }) => ({
                url: `/projects/${projectId}/members/bulk-add/`,
                method: "POST",
                body: data,
            }),
            transformResponse: (
                response: ApiResponse<BulkOperationResponse>,
            ) => {
                return response.data;
            },
            invalidatesTags: (result, error, { projectId }) => [
                { type: "Project", id: projectId },
                { type: "Project", id: "LIST" },
            ],
        }),

        // Remove member from project
        removeProjectMember: builder.mutation<
            ProjectDetail,
            { projectId: string; data: RemoveMemberData }
        >({
            query: ({ projectId, data }) => ({
                url: `/projects/${projectId}/members/remove/`,
                method: "POST",
                body: data,
            }),
            transformResponse: (response: ApiResponse<ProjectDetail>) => {
                return response.data;
            },
            invalidatesTags: (result, error, { projectId }) => [
                { type: "Project", id: projectId },
                { type: "Project", id: "LIST" },
            ],
        }),

        // Update member role
        updateMemberRole: builder.mutation<
            ProjectDetail,
            { projectId: string; data: UpdateMemberRoleData }
        >({
            query: ({ projectId, data }) => ({
                url: `/projects/${projectId}/members/role/`,
                method: "PATCH",
                body: data,
            }),
            transformResponse: (response: ApiResponse<ProjectDetail>) => {
                return response.data;
            },
            invalidatesTags: (result, error, { projectId }) => [
                { type: "Project", id: projectId },
                { type: "Project", id: "LIST" },
            ],
        }),

        // Update member tags
        updateMemberTags: builder.mutation<
            ProjectDetail,
            { projectId: string; data: UpdateMemberTagsData }
        >({
            query: ({ projectId, data }) => ({
                url: `/projects/${projectId}/members/tags/`,
                method: "PATCH",
                body: data,
            }),
            transformResponse: (response: ApiResponse<ProjectDetail>) => {
                return response.data;
            },
            invalidatesTags: (result, error, { projectId }) => [
                { type: "Project", id: projectId },
                { type: "Project", id: "LIST" },
            ],
        }),
    }),
});

// ============ Export Hooks ============

export const {
    // Queries
    useGetProjectsQuery,
    useGetProjectQuery,

    // CRUD Mutations
    useCreateProjectMutation,
    useUpdateProjectMutation,
    useDeleteProjectMutation,
    useGetWorkspaceMembersForDropdownQuery,
    // Status & Progress Mutations
    useUpdateProjectStatusMutation,
    useUpdateProjectProgressMutation,

    // Archive Mutation
    useArchiveProjectMutation,

    // Member Mutations
    useAddProjectMemberMutation,
    useBulkAddProjectMembersMutation,
    useRemoveProjectMemberMutation,
    useUpdateMemberRoleMutation,
    useUpdateMemberTagsMutation,
} = projectApiSlice;
