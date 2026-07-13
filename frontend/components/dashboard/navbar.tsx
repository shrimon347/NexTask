import { ThemeToggle } from "@/components/common/theme-toggle";
import { SheetMenu } from "@/components/dashboard/sheet-menu";
import { UserNav } from "@/components/dashboard/user-nav";
import { WorkspaceDropdown } from "./workspace-dropdown";

export function Navbar() {
    return (
        <header className="sticky top-0 z-10 w-full bg-background/95 shadow backdrop-blur supports-backdrop-filter:bg-background/60 dark:shadow-secondary">
            <div className="mx-4 sm:mx-8 flex h-14 items-center">
                <div className="flex items-center space-x-4 lg:space-x-0">
                    <SheetMenu />
                </div>
                <div className="flex flex-1 items-center justify-between gap-2">
                    <div>
                        <WorkspaceDropdown />
                    </div>
                    <div>
                        <ThemeToggle />
                        <UserNav />
                    </div>
                </div>
            </div>
        </header>
    );
}
