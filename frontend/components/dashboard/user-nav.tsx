"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/hooks/useAuth";
import { LogOutIcon, SettingsIcon, UserIcon } from "lucide-react";

export function UserNav() {
    const { data: user, isLoading, logout, isLoggingOut } = useAuth();
    const userInitial = user?.data?.name?.charAt(0)?.toUpperCase() || "U";
    const userEmail = user?.data?.email || "user@example.com";
    const userAvatar = user?.data?.avatar_url || undefined;

    if (isLoading) {
        return (
            <Button
                variant="outline"
                className="relative h-8 w-8 rounded-full"
                disabled
            >
                <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-transparent">
                        <span className="animate-pulse">...</span>
                    </AvatarFallback>
                </Avatar>
            </Button>
        );
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="outline"
                    className="relative h-8 w-8 rounded-full"
                >
                    <Avatar className="h-8 w-8">
                        <AvatarImage
                            src={userAvatar ?? "#"}
                            alt={user?.data?.name || "Avatar"}
                        />
                        <AvatarFallback className="bg-transparent">
                            {userInitial}
                        </AvatarFallback>
                    </Avatar>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
                <DropdownMenuItem>
                    <UserIcon />
                    Profile
                </DropdownMenuItem>

                <DropdownMenuItem>
                    <SettingsIcon />
                    Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                    variant="destructive"
                    onClick={logout}
                    disabled={isLoggingOut}
                >
                    <LogOutIcon />
                    {isLoggingOut ? "Logging out..." : "Log out"}
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
