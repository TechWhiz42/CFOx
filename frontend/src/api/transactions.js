const API =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000";

async function request(path, options = {}, authFetch) {
    if (typeof authFetch !== "function") {
        return fetch(`${API}${path}`, options);
    }

    return authFetch(`${API}${path}`, options);
}

export async function getTransactions(
    {limit = 20, offset = 0, signal} = {},
    authFetch
) {
    const query = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
    });

    return request(
        `/transactions?${query.toString()}`,
        {signal},
        authFetch
    );
}

export async function createTransaction(
    transaction,
    authFetch
) {
    return request(
        "/transactions",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(transaction),
        },
        authFetch
    );
}

export {API};
