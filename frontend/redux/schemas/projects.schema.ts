// schemas/projects.schema.ts

// ============ Base Response Types ============

export interface ProjectListItem {
    id: string;
    title: string;
    description: string;
    status: string;
    progress: number;
    start_date: string | null;
    due_date: string | null;
    is_archived: boolean;
    is_overdue: boolean;
    is_active: boolean;
    completion_summary: string;
    days_remaining: number | null;
    created_by: {
        id: string;
        email: string;
        name: string;
    };
    workspace: {
        id: string;
        name: string;
    };
    user_role: string | null;
    member_count: number;
    created_at: string;
    updated_at: string;
}

export interface ProjectMember {
    id: string;
    email: string;
    name: string;
    profile_picture: string | null;
    role: string;
    tags: string[];
    joined_at: string;
}

export interface ProjectDetail extends ProjectListItem {
    duration_days: number | null;
    status_color: string;
    members: ProjectMember[];
}

// ============ Query Params ============

export interface ProjectListQueryParams {
    workspaceId: string;
    status?: string;
    is_archived?: boolean;
    search?: string;
    sort_by?: string;
    sort_order?: string;
}

// ============ Mutation Data ============

export interface CreateProjectData {
    title: string;
    description?: string;
    status?: string;
    start_date?: string | null;
    due_date?: string | null;
    progress?: number;
    tags?: string;
    members?: Array<{
        user: string;
        role: string;
    }>;
}

export interface UpdateProjectData {
    title?: string;
    description?: string | null;
    status?: string;
    start_date?: string | null;
    due_date?: string | null;
    progress?: number;
    is_archived?: boolean;
    tags?: string | null;
    members?: Array<{
        user: string;
        role: string;
    }> | null;
}

export interface UpdateStatusData {
    status: string;
}

export interface UpdateProgressData {
    progress: number;
}

export interface ArchiveProjectData {
    is_archived: boolean;
}

export interface AddProjectMemberData {
    user_id: string;
    role?: string;
    tags?: string[];
}

export interface BulkAddMembersData {
    members: Array<{
        user: string;
        role: string;
    }>;
}

export interface RemoveMemberData {
    user_id: string;
}

export interface UpdateMemberRoleData {
    user_id: string;
    role: string;
}

export interface UpdateMemberTagsData {
    user_id: string;
    tags: string[];
}

// ============ Bulk Operation Response ============

export interface BulkOperationFailedItem {
    user: string;
    email?: string;
    error: string;
}

export interface BulkOperationResponse {
    project: ProjectDetail;
    added: string[];
    failed: BulkOperationFailedItem[];
}
