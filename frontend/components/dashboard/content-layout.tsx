import { Navbar } from "@/components/dashboard/navbar";

interface ContentLayoutProps {
    title: string;
    children: React.ReactNode;
    header?: React.ReactNode;
}

export function ContentLayout({ title, header, children }: ContentLayoutProps) {
    return (
        <div>
            <Navbar />
            <div className="container pt-8 pb-8 px-4 sm:px-8">
                <div className="flex justify-between items-center">
                    <h1 className="font-bold text-3xl text-primary">{title}</h1>
                    {header && <div className="mb-6">{header}</div>}
                </div>
                {children}
            </div>
        </div>
    );
}
