"use client";

import { Spinner } from "@/components/ui/spinner";
import { useRetrieveUserQuery } from "@/redux/features/authApiSlice";

export default function Page() {
    const { data: user, isLoading, isFetching } = useRetrieveUserQuery();


    if (isLoading || isFetching) {
        return (
            <div className="flex justify-center my-8">
                <Spinner className="size-10" />
            </div>
        );
    }

    return (
        <>
            <header className="bg-white shadow">
                <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900">
                        Dashboard
                    </h1>
                </div>
            </header>
            <main className="mx-auto max-w-7xl py-6 my-8 sm:px-6 lg:px-8">
                <p>{user?.data.name}</p>
            </main>
        </>
    );
}
