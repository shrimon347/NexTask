import {
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbLink,
    BreadcrumbList,
    BreadcrumbPage,
    BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import Link from "next/link";

export function DashboardBreadcrumb({ page }: { page: string }) {
    return (
        <Breadcrumb>
            <BreadcrumbList>
                <BreadcrumbItem>
                    <BreadcrumbLink render={<Link href="/">Home</Link>} />
                </BreadcrumbItem>

                <BreadcrumbSeparator />

                <BreadcrumbItem>
                    <BreadcrumbPage>{page}</BreadcrumbPage>
                </BreadcrumbItem>
            </BreadcrumbList>
        </Breadcrumb>
    );
}
