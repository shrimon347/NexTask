import { apiSlice } from "../services/apiSlice";

interface User {
    id: string;
    email: string;
    name: string;
    avatar_url: string;
    is_email_verified: boolean;
    is_2fa_enabled: boolean;
    created_at: string;
    updated_at: string;
}
interface SocialAuthArgs {
    provider: string;
    state: string;
    code: string;
}

interface CreateUserResponse {
    success: boolean;
    user: User;
}

const authApiSlice = apiSlice.injectEndpoints({
    endpoints: (builder) => ({
        retrieveUser: builder.query<User, void>({
            query: () => "/auth/me/",
        }),
        socialAuthenticate: builder.mutation<
            CreateUserResponse,
            SocialAuthArgs
        >({
            query: ({ provider, state, code }) => ({
                url: `/auth/o/${provider}/?state=${encodeURIComponent(
                    state,
                )}&code=${encodeURIComponent(code)}`,
                method: "POST",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            }),
        }),
        login: builder.mutation({
            query: ({ email, password }) => ({
                url: "/auth/login/",
                method: "POST",
                body: { email, password },
            }),
        }),
        register: builder.mutation({
            query: ({ name, email, password, re_password }) => ({
                url: "/auth/register/",
                method: "POST",
                body: { name, email, password, re_password },
            }),
        }),
        verify: builder.mutation({
            query: () => ({
                url: "/auth/verify/",
                method: "POST",
            }),
        }),
        logout: builder.mutation({
            query: () => ({
                url: "/auth/logout/",
                method: "POST",
                credentials: "include",
            }),
        }),
        activation: builder.mutation({
            query: ({ uid, token }) => ({
                url: "/auth/activation/",
                method: "POST",
                body: { uid, token },
            }),
        }),
        resendActivation: builder.mutation({
            query: ({ email }) => ({
                url: "/auth/resend-activation/",
                method: "POST",
                body: { email },
            }),
        }),
        resetPassword: builder.mutation({
            query: (email) => ({
                url: "/auth/password/reset/",
                method: "POST",
                body: { email },
            }),
        }),
        resetPasswordConfirm: builder.mutation({
            query: ({ uid, token, new_password, re_new_password }) => ({
                url: "/auth/password/reset/confirm/",
                method: "POST",
                body: { uid, token, new_password, re_new_password },
            }),
        }),
    }),
});

export const {
    useRetrieveUserQuery,
    useSocialAuthenticateMutation,
    useLoginMutation,
    useRegisterMutation,
    useVerifyMutation,
    useLogoutMutation,
    useActivationMutation,
    useResendActivationMutation,
    useResetPasswordMutation,
    useResetPasswordConfirmMutation,
} = authApiSlice;
