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
import { useLogoutMutation } from "@/redux/features/authApiSlice";
import { logout as setLogout } from "@/redux/features/authSlice";
import { useAppDispatch } from "@/redux/hooks";
import { LogOutIcon, SettingsIcon, UserIcon } from "lucide-react";
import { useRouter } from "next/navigation";

export function UserNav() {
    const router = useRouter();
    const dispatch = useAppDispatch();
    const { user, isLoading } = useAuth();
    const [logoutUser] = useLogoutMutation();

    // User data is directly on the user object
    const userInitial = user?.name?.charAt(0)?.toUpperCase() || "U";
    const userEmail = user?.email || "user@example.com";
    const userAvatar = user?.avatar_url || undefined;

    const handleLogout = async () => {
        try {
            await logoutUser().unwrap();
            dispatch(setLogout());
            router.push("/signin");
        } catch (error) {
            console.error("Logout error:", error);
        }
    };

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
                            alt={user?.name || "Avatar"}
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
                <DropdownMenuItem variant="destructive" onClick={handleLogout}>
                    <LogOutIcon />
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
