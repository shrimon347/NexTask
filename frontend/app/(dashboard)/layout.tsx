import DashboardLayout from "@/components/dashboard/dashboardLayout";
import { RequireAuth } from "@/components/utils";
interface Props {
    children: React.ReactNode;
}

export default function Layout({ children }: Props) {
    return <RequireAuth><DashboardLayout>{children}</DashboardLayout></RequireAuth>;
}
