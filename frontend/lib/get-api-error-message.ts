type ApiErrorOptions = {
    fallback: string;
    separator?: string;
};

/**
 * Normalizes RTK Query / fetch errors (including DRF-style
 * `{ field: ["msg"] }` validation payloads) into a single
 * human-readable string.
 */
export function getApiErrorMessage(
    error: unknown,
    { fallback, separator = "\n" }: ApiErrorOptions,
): string {
    if (!error || typeof error !== "object") return fallback;

    const err = error as { data?: unknown; status?: number; message?: string };

    // RTK Query fetch errors put the server payload in `data`
    const data = err.data ?? error;

    if (typeof data === "string") return data;

    if (data && typeof data === "object") {
        const messages: string[] = [];

        for (const [key, value] of Object.entries(
            data as Record<string, unknown>,
        )) {
            if (Array.isArray(value)) {
                messages.push(
                    key === "non_field_errors" || key === "detail"
                        ? value.join(" ")
                        : `${key}: ${value.join(" ")}`,
                );
            } else if (typeof value === "string") {
                messages.push(key === "detail" ? value : `${key}: ${value}`);
            }
        }

        if (messages.length) return messages.join(separator);
    }

    if (typeof err.message === "string" && err.message) return err.message;

    return fallback;
}
