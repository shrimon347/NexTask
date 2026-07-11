"use client";

import { Field, FieldSeparator } from "@/components/ui/field";
import { continueWithGithub, continueWithGoogle } from "@/utils";
import { SocialLoginButton } from "./SocialLoginButton";

interface SocialLoginSectionProps {
    className?: string;
}

export function SocialLoginSection({ className }: SocialLoginSectionProps) {
    return (
        <>
            <FieldSeparator>Or continue with</FieldSeparator>

            <Field className={className}>
                <div className="space-y-3">
                    <SocialLoginButton
                        provider="google"
                        onClick={continueWithGoogle}
                    />
                    <SocialLoginButton
                        provider="github"
                        onClick={continueWithGithub}
                    />
                </div>
            </Field>
        </>
    );
}
