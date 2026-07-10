// app/providers.tsx
"use client";

import { Toaster } from "@/components/ui/sonner";
import { Spinner } from "@/components/ui/spinner";
import Setup from "@/components/utils/Setup";
import Provider from "@/redux/provider";
import { ThemeProvider } from "next-themes";
import { Suspense } from "react";

type ProvidersProps = {
    children: React.ReactNode;
};

export function Providers({ children }: ProvidersProps) {
    return (
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            <Provider>
                <Suspense
                    fallback={
                        <div className="flex justify-center items-center min-h-screen">
                            <Spinner className="size-10" />
                        </div>
                    }
                >
                    <Setup />
                </Suspense>
                {children}
                <Toaster position="top-center" richColors closeButton />
            </Provider>
        </ThemeProvider>
    );
}
