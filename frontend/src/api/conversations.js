const API =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000";

async function requestJson(
    url,
    options = {},
    authFetch
) {
    const request = authFetch || fetch;

    const response = await request(
        `${API}${url}`,
        {
            ...options,
            headers: {
                ...(options.body
                    ? {
                        "Content-Type": "application/json",
                    }
                    : {}),
                ...(options.headers || {}),
            },
        }
    );

    let data = null;

    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok) {
        throw new Error(
            data?.detail ||
            `Request failed: ${response.status}`
        );
    }

    return data;
}

export function listConversations(authFetch) {
    return requestJson(
        "/transactions/cfo/conversations",
        {},
        authFetch
    );
}

export function createConversation(
    title = null,
    authFetch
) {
    return requestJson(
        "/transactions/cfo/conversations",
        {
            method: "POST",
            body: JSON.stringify({
                title,
            }),
        },
        authFetch
    );
}

export function getConversation(
    conversationId,
    authFetch
) {
    return requestJson(
        `/transactions/cfo/conversations/${conversationId}`,
        {},
        authFetch
    );
}

export function sendConversationMessage(
    conversationId,
    content,
    authFetch
) {
    return requestJson(
        `/transactions/cfo/conversations/${conversationId}/messages`,
        {
            method: "POST",
            body: JSON.stringify({
                content,
            }),
        },
        authFetch
    );
}

export function deleteConversation(
    conversationId,
    authFetch
) {
    return requestJson(
        `/transactions/cfo/conversations/${conversationId}`,
        {
            method: "DELETE",
        },
        authFetch
    );
}

export async function streamConversationMessage(
    conversationId,
    content,
    authFetch,
    {
        onMetadata,
        onToken,
        onDone,
        onError,
    } = {}
) {
    const request = authFetch || fetch;

    const response = await request(
        `${API}/transactions/cfo/conversations/${conversationId}/messages/stream`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                content,
            }),
        }
    );

    if (!response.ok) {
        let detail = `Request failed: ${response.status}`;

        try {
            const data = await response.json();

            if (data?.detail) {
                detail = data.detail;
            }
        } catch {
            // Keep default error.
        }

        throw new Error(detail);
    }

    if (!response.body) {
        throw new Error(
            "Streaming is not supported by this browser."
        );
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";

    try {
        while (true) {
            const {value, done} =
                await reader.read();

            if (done) {
                break;
            }

            buffer += decoder.decode(
                value,
                {stream: true}
            );

            const lines = buffer.split("\n");

            buffer = lines.pop() || "";

            for (const line of lines) {
                const trimmed = line.trim();

                if (!trimmed) {
                    continue;
                }

                let event;

                try {
                    event = JSON.parse(trimmed);
                } catch {
                    continue;
                }

                if (event.type === "metadata") {
                    onMetadata?.(event);
                } else if (event.type === "token") {
                    onToken?.(
                        event.content || ""
                    );
                } else if (event.type === "done") {
                    onDone?.(event);
                } else if (event.type === "error") {
                    const error = new Error(
                        event.detail ||
                        "CFO streaming failed."
                    );

                    onError?.(error);

                    throw error;
                }
            }
        }

        if (buffer.trim()) {
            try {
                const event = JSON.parse(
                    buffer.trim()
                );

                if (event.type === "metadata") {
                    onMetadata?.(event);
                } else if (event.type === "token") {
                    onToken?.(
                        event.content || ""
                    );
                } else if (event.type === "done") {
                    onDone?.(event);
                } else if (event.type === "error") {
                    const error = new Error(
                        event.detail ||
                        "CFO streaming failed."
                    );

                    onError?.(error);

                    throw error;
                }
            } catch (error) {
                if (
                    error instanceof Error &&
                    error.message !==
                    "Unexpected end of JSON input"
                ) {
                    throw error;
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}

export {API};

