import { apiSlice } from "./apiSlice";

export interface Workspace {
    id: string;
    name: string;
    description?: string;
    color?: string;
    owner: string;
    members: string[];
    created_at: string;
    updated_at: string;
    is_active: boolean;
}

export interface CreateWorkspaceData {
    name: string;
    description?: string;
    color?: string;
}

export const workspaceApiSlice = apiSlice.injectEndpoints({
    endpoints: (builder) => ({
        // Get all workspaces
        getWorkspaces: builder.query<Workspace[], void>({
            query: () => "/workspaces/",
            providesTags: ["Workspace"],
        }),

        // Get single workspace
        getWorkspace: builder.query<Workspace, string>({
            query: (id) => `/workspaces/${id}/`,
            providesTags: (result, error, id) => [{ type: "Workspace", id }],
        }),

        // Create workspace
        createWorkspace: builder.mutation<Workspace, CreateWorkspaceData>({
            query: (data) => ({
                url: "/workspaces/",
                method: "POST",
                body: data,
            }),
            invalidatesTags: ["Workspace"],
        }),

        // Update workspace
        updateWorkspace: builder.mutation<
            Workspace,
            { id: string; data: Partial<Workspace> }
        >({
            query: ({ id, data }) => ({
                url: `/workspaces/${id}/`,
                method: "PATCH",
                body: data,
            }),
            invalidatesTags: (result, error, { id }) => [
                { type: "Workspace", id },
                "Workspace",
            ],
        }),

        // Delete workspace
        deleteWorkspace: builder.mutation<void, string>({
            query: (id) => ({
                url: `/workspaces/${id}/`,
                method: "DELETE",
            }),
            invalidatesTags: ["Workspace"],
        }),
    }),
});

export const {
    useGetWorkspacesQuery,
    useGetWorkspaceQuery,
    useCreateWorkspaceMutation,
    useUpdateWorkspaceMutation,
    useDeleteWorkspaceMutation,
} = workspaceApiSlice;
