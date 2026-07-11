"use client";

import { useAppSelector } from "@/redux/hooks";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Spinner } from "../ui/spinner";

interface Props {
    children: React.ReactNode;
}

export default function RequireAuth({ children }: Props) {
    const { isLoading, isAuthenticated } = useAppSelector(
        (state) => state.auth,
    );
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace("/signin");
        }
    }, [isLoading, isAuthenticated, router]);

    if (isLoading || !isAuthenticated) {
        return (
            <div className="flex justify-center my-8">
                <Spinner className="size-10" />
            </div>
        );
    }

    return <>{children}</>;
}
