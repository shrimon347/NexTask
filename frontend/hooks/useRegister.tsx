import { useRegisterMutation } from "@/redux/features/authApiSlice";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { toast } from "sonner";
import { CheckCircle } from "lucide-react";

interface RegisterData {
    name: string;
    email: string;
    password: string;
    re_password: string;
}

export function useRegister() {
    const router = useRouter();
    const [register, { isLoading }] = useRegisterMutation();
    const [submitError, setSubmitError] = useState<string | null>(null);

    const handleRegister = useCallback(
        async (data: RegisterData) => {
            setSubmitError(null);

            try {
                await register(data).unwrap();

                toast.success("Account created successfully!", {
                    description:"Please check your email to verify your account.",
                    icon: <CheckCircle className="text-green-500"/>,   
                });

                router.push("/signin");
            } catch (error: unknown) {
                const errorMessage =
                    error?.data?.message ||
                    error?.data?.error ||
                    "Failed to register account. Please try again.";

                setSubmitError(errorMessage);

                toast.error("Registration failed", {
                    description: errorMessage,
                });
            }
        },
        [register, router],
    );

    return {
        handleRegister,
        isLoading,
        submitError,
        setSubmitError,
    };
}
