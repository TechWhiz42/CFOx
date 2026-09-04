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

export async function getConversation(
    conversationId,
    options = {},
    authFetch
) {
    return request(
        `/cfo/conversations/${conversationId}`,
        options,
        authFetch
    );
}

export async function deleteConversation(
    conversationId,
    options = {},
    authFetch
) {
    return request(
        `/cfo/conversations/${conversationId}`,
        {
            ...options,
            method: "DELETE",
        },
        authFetch
    );
}

export async function renameConversation(
    conversationId,
    title,
    options = {},
    authFetch
) {
    return request(
        `/cfo/conversations/${conversationId}`,
        {
            ...options,
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
            body: JSON.stringify({ title }),
        },
        authFetch
    );
}

export { API };