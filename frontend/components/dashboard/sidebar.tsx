"use client";

import { Menu } from "@/components/dashboard/menu";
import { SidebarToggle } from "@/components/dashboard/sidebar-toggle";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { setIsHover, toggleOpen } from "@/redux/features/sidebarSlice";
import {
    selectSidebarOpenState,
    useAppDispatch,
    useAppSelector,
} from "@/redux/hooks";
import { PanelsTopLeft } from "lucide-react";
import Link from "next/link";

export function Sidebar() {
    const dispatch = useAppDispatch();

    const isOpen = useAppSelector((state) => state.sidebar.isOpen);
    const settings = useAppSelector((state) => state.sidebar.settings);
    const openState = useAppSelector(selectSidebarOpenState);

    if (settings.disabled) return null;

    return (
        <aside
            className={cn(
                "fixed top-0 left-0 z-20 h-screen -translate-x-full lg:translate-x-0 transition-[width] ease-in-out duration-300",
                !openState ? "w-[90px]" : "w-72",
            )}
        >
            <SidebarToggle
                isOpen={isOpen}
                setIsOpen={() => dispatch(toggleOpen())}
            />

            <div
                onMouseEnter={() => dispatch(setIsHover(true))}
                onMouseLeave={() => dispatch(setIsHover(false))}
                className="relative h-full flex flex-col px-3 py-4 overflow-y-auto shadow-md dark:shadow-zinc-800"
            >
                <Button
                    className={cn(
                        "transition-transform ease-in-out duration-300 mb-1",
                        !openState ? "translate-x-1" : "translate-x-0",
                    )}
                    variant="link"
                    asChild
                >
                    <Link href="/dashboard" className="flex items-center gap-2">
                        <PanelsTopLeft className="w-6 h-6 mr-1" />

                        <h1
                            className={cn(
                                "font-bold text-lg whitespace-nowrap transition-[transform,opacity,display] ease-in-out duration-300",
                                !openState
                                    ? "-translate-x-96 opacity-0 hidden"
                                    : "translate-x-0 opacity-100",
                            )}
                        >
                            Brand
                        </h1>
                    </Link>
                </Button>

                <Menu isOpen={openState} />
            </div>
        </aside>
    );
}
