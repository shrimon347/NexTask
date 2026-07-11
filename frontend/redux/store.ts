import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./features/authSlice";
import sidebarReducer from "./features/sidebarSlice";
import { apiSlice } from "./services/apiSlice";

export const store = configureStore({
    reducer: {
        [apiSlice.reducerPath]: apiSlice.reducer,
        auth: authReducer,
        sidebar: sidebarReducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware().concat(apiSlice.middleware),
    devTools: process.env.NODE_ENV !== "production",
});

export type RootState = ReturnType<(typeof store)["getState"]>;
export type AppDispatch = (typeof store)["dispatch"];
