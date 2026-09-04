const API =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000";


async function request(path, options = {}, authFetch) {
    const fetcher = authFetch || fetch;

    return fetcher(`${API}${path}`, {
        ...options,
        headers: {
            ...(options.headers || {}),
        },
    });
}


export async function getDashboard(
    paymentMethod = "all",
    options = {},
    authFetch
) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return request(
        `/transactions/dashboard${query}`,
        options,
        authFetch
    );
}


export async function getPaymentMethods(
    options = {},
    authFetch
) {
    return request(
        "/transactions/analytics/payment-methods",
        options,
        authFetch
    );
}


export async function getRevenueHistory(
    paymentMethod = "all",
    days = 30,
    options = {},
    authFetch
) {
    const query =
        paymentMethod === "all"
            ? `?days=${days}`
            : `?days=${days}&payment_method=${encodeURIComponent(
                  paymentMethod
              )}`;

    return request(
        `/transactions/analytics/revenue-history${query}`,
        options,
        authFetch
    );
}


export async function getAnomaly(
    paymentMethod = "all",
    options = {},
    authFetch
) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return request(
        `/transactions/analytics/anomaly${query}`,
        options,
        authFetch
    );
}


export async function getAlerts(
    paymentMethod = "all",
    options = {},
    authFetch
) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return request(
        `/transactions/alerts${query}`,
        options,
        authFetch
    );
}


export async function getAIInsight(
    paymentMethod = "all",
    options = {},
    authFetch
) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return request(
        `/transactions/analytics/ai-insight${query}`,
        options,
        authFetch
    );
}


export async function getFinancialHealth(
    paymentMethod = "all",
    options = {},
    authFetch
) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return request(
        `/transactions/analytics/financial-health${query}`,
        options,
        authFetch
    );
}


export async function getFinancialActions(
    paymentMethod = "all",
    options = {},
    authFetch
) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return request(
        `/transactions/analytics/financial-actions${query}`,
        options,
        authFetch
    );
}


export { API };