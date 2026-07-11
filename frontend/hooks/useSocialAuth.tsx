"use client";

import { setAuth } from "@/redux/features/authSlice";
import { useAppDispatch } from "@/redux/hooks";
import { CheckCircle, XCircle } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef } from "react";
import { toast } from "sonner";

interface SocialAuthData {
    provider: string;
    state: string;
    code: string;
}

const PROVIDER_NAMES: Record<string, string> = {
    google: "google-oauth2",
    github: "GitHub",
};

function getProviderName(provider: string): string {
    return PROVIDER_NAMES[provider.toLowerCase()] || provider;
}

export default function useSocialAuth(
    authenticate: (data: SocialAuthData) => Promise<unknown>,
    provider: string,
) {
    const dispatch = useAppDispatch();
    const router = useRouter();
    const searchParams = useSearchParams();

    const effectRan = useRef(false);
    const providerName = getProviderName(provider);

    useEffect(() => {
        const state = searchParams.get("state");
        const code = searchParams.get("code");

        if (state && code && !effectRan.current) {
            authenticate({ provider, state, code })
                .unwrap()
                .then(() => {
                    dispatch(setAuth());
                    toast.success(`Welcome!`, {
                        description: `Successfully logged in with ${providerName}.`,
                        icon: <CheckCircle className="text-green-500 size-5" />,
                        duration: 5000,
                    });
                    router.push("/dashboard");
                })
                .catch((error: unknown) => {
                    const errorMessage =
                        error?.data?.message ||
                        error?.data?.error ||
                        `Failed to log in with ${providerName}. Please try again.`;

                    toast.error("Login failed", {
                        description: errorMessage,
                        icon: <XCircle className="text-red-500 size-5" />,
                        duration: 5000,
                    });
                    router.push("/signin");
                });
        }

        return () => {
            effectRan.current = true;
        };
    }, [authenticate, provider, providerName, searchParams, dispatch, router]);
}
