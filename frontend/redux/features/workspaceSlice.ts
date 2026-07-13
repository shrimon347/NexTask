
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Workspace } from "../services/workspaceApiSlice";

interface WorkspaceState {
    selectedWorkspace: Workspace | null;
}

const initialState: WorkspaceState = {
    selectedWorkspace: null,
};

const workspaceSlice = createSlice({
    name: "workspace",
    initialState,
    reducers: {
        setSelectedWorkspace: (
            state,
            action: PayloadAction<Workspace | null>,
        ) => {
            state.selectedWorkspace = action.payload;
        },
        clearSelectedWorkspace: (state) => {
            state.selectedWorkspace = null;
        },
    },
});

export const { setSelectedWorkspace, clearSelectedWorkspace } =
    workspaceSlice.actions;
export default workspaceSlice.reducer;
