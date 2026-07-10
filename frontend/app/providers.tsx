"use client";

import { Toaster } from "@/components/ui/sonner";
import Provider from "@/redux/provider";
import { ThemeProvider } from "next-themes";
type ProvidersProps = {
    children: React.ReactNode;
};

export function Providers({ children }: ProvidersProps) {
    return (
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            <Provider>
                {children}
                <Toaster position="top-center" />
            </Provider>
        </ThemeProvider>
    );
}
