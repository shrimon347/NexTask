"use client";

import { Spinner } from "@/components/ui/spinner";
import useSocialAuth from "@/hooks/useSocialAuth";
import { useSocialAuthenticateMutation } from "@/redux/features/authApiSlice";

export default function Page() {
    const [googleAuthenticate] = useSocialAuthenticateMutation();
    useSocialAuth(googleAuthenticate, "google-oauth2");

    return (
        <div className="my-8">
            <Spinner className="size-10" />
        </div>
    );
}
