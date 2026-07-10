"use client";

import { useAppSelector } from "@/redux/hooks";
import { redirect } from "next/navigation";
import { Spinner } from "../ui/spinner";

interface Props {
    children: React.ReactNode;
}

export default function RequireAuth({ children }: Props) {
    const { isLoading, isAuthenticated } = useAppSelector(
        (state) => state.auth,
    );

    if (isLoading) {
        return (
            <div className="flex justify-center my-8">
                <Spinner className="size-10" />
            </div>
        );
    }

    if (!isAuthenticated) {
        redirect("/signin");
    }

    return <>{children}</>;
}
