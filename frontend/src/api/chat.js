const API =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000";

export async function streamCFOChat(
    question,
    options = {}
) {
    return fetch(
        `${API}/transactions/cfo/chat`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                question,
            }),
            signal: options.signal,
        }
    );
}

export { API };