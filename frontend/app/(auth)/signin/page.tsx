import { GalleryVerticalEnd } from "lucide-react";

import { LoginForm } from "@/components/auth/signin-form";
import { ThemeToggle } from "@/components/common/theme-toggle";
import Image from "next/image";

export default function LoginPage() {
    return (
        <div className="grid min-h-svh lg:grid-cols-2">
            <div className="relative hidden bg-muted lg:block">
                <Image
                    width={20}
                    height={20}
                    src="/placeholder.svg"
                    alt="Image"
                    className="absolute inset-0 h-full w-full object-cover dark:brightness-[0.2] dark:grayscale"
                />
            </div>
            <div className="flex flex-col gap-4 p-6 md:p-10">
                <div className="flex items-center justify-between gap-4">
                    <div className="flex justify-center gap-2 md:justify-start">
                        <a
                            href="#"
                            className="flex items-center gap-2 font-medium"
                        >
                            <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
                                <GalleryVerticalEnd className="size-4" />
                            </div>
                            Acme Inc.
                        </a>
                    </div>
                    <ThemeToggle />
                </div>
                <div className="flex flex-1 items-center justify-center">
                    <div className="w-full max-w-xs">
                        <LoginForm />
                    </div>
                </div>
            </div>
        </div>
    );
}
