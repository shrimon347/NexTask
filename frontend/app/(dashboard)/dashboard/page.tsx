"use client";

import { SidebarSettings } from "@/components/dashboard/sidebar-settings";
import { Spinner } from "@/components/ui/spinner";
import { useRetrieveUserQuery } from "@/redux/features/authApiSlice";

export default function Page() {
    const { data: user, isLoading, isFetching } = useRetrieveUserQuery();

    if (isLoading || isFetching) {
        return (
            <div className="flex justify-center items-center my-8">
                <Spinner className="size-10" />
            </div>
        );
    }

    return (
        <>
            <SidebarSettings />
        </>
    );
}
