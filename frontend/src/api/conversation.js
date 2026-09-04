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
                        "Content-Type":
                            "application/json",
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

export {API};