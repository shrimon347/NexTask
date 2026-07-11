"use client";

import { ContentLayout } from "@/components/dashboard/content-layout";
import { DashboardBreadcrumb } from "@/components/dashboard/dashboard-breadcrumb";
import { Footer } from "@/components/dashboard/footer";
import { Sidebar } from "@/components/dashboard/sidebar";
import { cn } from "@/lib/utils";
import { selectSidebarOpenState, useAppSelector } from "@/redux/hooks";
import { usePathname } from "next/navigation";


export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const settings = useAppSelector((state) => state.sidebar.settings);
    const openState = useAppSelector(selectSidebarOpenState);

    const pathname = usePathname();

    let title = "Dashboard";
    if (pathname.startsWith("/workspace")) title = "Workspace";

    return (
        <>
            <Sidebar />

            <main
                className={cn(
                    "min-h-[calc(100vh-56px)] bg-zinc-50 dark:bg-zinc-900 transition-[margin-left] ease-in-out duration-300",
                    !settings.disabled &&
                        (!openState ? "lg:ml-[90px]" : "lg:ml-72"),
                )}
            >
                <ContentLayout
                    title={title}
                    header={<DashboardBreadcrumb page={title} />}
                >
                    {children}
                </ContentLayout>
            </main>

            <footer
                className={cn(
                    "transition-[margin-left] ease-in-out duration-300",
                    !settings.disabled &&
                        (!openState ? "lg:ml-[90px]" : "lg:ml-72"),
                )}
            >
                <Footer />
            </footer>
        </>
    );
}
