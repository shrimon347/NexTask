// components/workspaces/workspace-avatar.tsx
interface WorkspaceAvatarProps {
    color?: string;
    name?: string;
    size?: "sm" | "md" | "lg";
}

export function WorkspaceAvatar({
    color,
    name,
    size = "md",
}: WorkspaceAvatarProps) {
    const sizes = {
        sm: "w-6 h-6 text-xs",
        md: "w-8 h-8 text-sm",
        lg: "w-10 h-10 text-base",
    };

    // ✅ FIX: Check if name exists before calling charAt
    const firstLetter = name?.charAt(0)?.toUpperCase() || "W";

    return (
        <div
            className={`${sizes[size]} rounded-full flex items-center justify-center font-semibold text-white shrink-0`}
            style={{ backgroundColor: color || "#6366f1" }}
        >
            <span className="text-xs font-medium text-white">
                {firstLetter}
            </span>
        </div>
    );
}
