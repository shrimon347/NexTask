"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { setSettings } from "@/redux/features/sidebarSlice";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";

export function SidebarSettings() {
    const dispatch = useAppDispatch();
    const settings = useAppSelector((state) => state.sidebar.settings);

    return (
        <TooltipProvider>
            <div className="flex gap-6 mt-6">
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div className="flex items-center space-x-2">
                            <Switch
                                checked={settings.isHoverOpen}
                                onCheckedChange={(value) =>
                                    dispatch(
                                        setSettings({ isHoverOpen: value }),
                                    )
                                }
                            />
                            <Label>Hover Open</Label>
                        </div>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>When hovering sidebar, it opens</p>
                    </TooltipContent>
                </Tooltip>

                <Tooltip>
                    <TooltipTrigger asChild>
                        <div className="flex items-center space-x-2">
                            <Switch
                                checked={settings.disabled}
                                onCheckedChange={(value) =>
                                    dispatch(setSettings({ disabled: value }))
                                }
                            />
                            <Label>Disable Sidebar</Label>
                        </div>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Hide sidebar</p>
                    </TooltipContent>
                </Tooltip>
            </div>
        </TooltipProvider>
    );
}
