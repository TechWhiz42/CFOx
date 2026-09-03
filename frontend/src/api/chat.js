const API =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000";

/**
 * Stream the authenticated CFO chat endpoint.
 *
 * authFetch is supplied by AuthContext so protected backend
 * endpoints receive the current JWT.
 */
export async function streamCFOChat(
    question,
    options = {},
    authFetch
) {
    const request = authFetch || fetch;

    return request(
        `${API}/transactions/cfo/chat`,
        {
            method: "POST",
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
            body: JSON.stringify({
                question,
            }),
        }
    );
}

export { API };