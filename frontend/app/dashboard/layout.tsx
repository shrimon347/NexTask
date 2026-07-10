import { RequireAuth } from "@/components/utils";
interface Props {
    children: React.ReactNode;
}

export default function DashboardLayout({ children }: Props) {
    return <RequireAuth>{children}</RequireAuth>;
}
