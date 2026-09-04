import {API} from "./config";

async function request(path, options = {}, authFetch) {
    const fetcher = authFetch || fetch;

    return fetcher(`${API}${path}`, {
        ...options,
        headers: {
            ...(options.headers || {}),
        },
    });
}

export async function sendChatMessage(
    message,
    conversationId = null,
    options = {},
    authFetch
) {
    return request(
        "/cfo/chat",
        {
            ...options,
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
            body: JSON.stringify({
                message,
                conversation_id: conversationId,
            }),
        },
        authFetch
    );
}

export { API };