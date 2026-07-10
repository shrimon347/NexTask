"use client";

import { useActivationMutation } from "@/redux/features/authApiSlice";
import { CheckCircle, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

interface Props {
    params: Promise<{
        uid: string;
        token: string;
    }>;
}

export default function ActivationPage({ params }: Props) {
    const router = useRouter();
    const [activation, { isLoading }] = useActivationMutation();
    const [error, setError] = useState<string | null>(null);
    const [isSuccess, setIsSuccess] = useState(false);

    // ✅ Use React.use() to unwrap the Promise
    const { uid, token } = React.use(params);

    useEffect(() => {
        activation({ uid, token })
            .unwrap()
            .then(() => {
                setIsSuccess(true);
                toast.success("Account activated successfully!", {
                    description:
                        "Your account has been verified. You can now login.",
                    icon: <CheckCircle className="text-green-500 size-5" />,
                    duration: 5000,
                });
                setTimeout(() => router.push("/signin"), 3000);
            })
            .catch((error: unknown) => {
                const errorMessage =
                    error?.data?.message ||
                    error?.data?.error ||
                    "Failed to activate account. The link may be invalid or expired.";
                setError(errorMessage);
                toast.error("Activation failed", {
                    description: errorMessage,
                    icon: <XCircle className="text-red-500 size-5" />,
                    duration: 5000,
                });
            });
    }, [activation, uid, token, router]);

    // Loading, success, error states...
    if (isLoading) {
        return (
            <div className="flex min-h-[80vh] flex-col items-center justify-center px-6 py-12">
                <div className="sm:mx-auto sm:w-full sm:max-w-sm text-center">
                    <Spinner className="size-12 mx-auto mb-6" aria-hidden />
                    <h1 className="text-2xl font-bold">
                        Activating your account...
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Please wait while we verify your account.
                    </p>
                </div>
            </div>
        );
    }

    if (isSuccess) {
        return (
            <div className="flex min-h-[80vh] flex-col items-center justify-center px-6 py-12">
                <div className="sm:mx-auto sm:w-full sm:max-w-sm text-center">
                    <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20 mb-6">
                        <CheckCircle className="size-10 text-green-600 dark:text-green-400" />
                    </div>
                    <h1 className="text-2xl font-bold">
                        Account Activated! 🎉
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Your account has been successfully verified.
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Redirecting you to login...
                    </p>
                    <Button
                        onClick={() => router.push("/signin")}
                        className="mt-6 w-full"
                    >
                        Go to Login
                    </Button>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex min-h-[80vh] flex-col items-center justify-center px-6 py-12">
                <div className="sm:mx-auto sm:w-full sm:max-w-sm text-center">
                    <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20 mb-6">
                        <XCircle className="size-10 text-red-600 dark:text-red-400" />
                    </div>
                    <h1 className="text-2xl font-bold">Activation Failed</h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        {error}
                    </p>
                    <div className="mt-6 space-y-3">
                        <Button
                            onClick={() => router.push("/resend/activation/email")}
                            className="w-full"
                        >
                            Resend Verification Email
                        </Button>
                        <Button
                            variant="outline"
                            onClick={() => router.push("/signin")}
                            className="w-full"
                        >
                            Back to Login
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    return null;
}
