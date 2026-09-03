const API =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000";

async function request(path, options = {}) {
    return fetch(`${API}${path}`, options);
}

export async function getDashboard(
    paymentMethod,
    options = {}
) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(
                  paymentMethod
              )}`;

    return request(
        `/transactions/dashboard${query}`,
        options
    );
}

export async function getPaymentMethods(
    options = {}
) {
    return request(
        "/transactions/analytics/payment-methods",
        options
    );
}

export async function getRevenueHistory(
    paymentMethod,
    days = 30,
    options = {}
) {
    const query =
        paymentMethod === "all"
            ? `?days=${days}`
            : `?days=${days}&payment_method=${encodeURIComponent(
                  paymentMethod
              )}`;

    return request(
        `/transactions/analytics/revenue-history${query}`,
        options
    );
}

export async function getAnomaly(
    paymentMethod,
    options = {}
) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(
                  paymentMethod
              )}`;

    return request(
        `/transactions/analytics/anomaly${query}`,
        options
    );
}

export async function getAlerts(
    paymentMethod,
    options = {}
) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(
                  paymentMethod
              )}`;

    return request(
        `/transactions/alerts${query}`,
        options
    );
}

export async function getAIInsight(
    paymentMethod,
    options = {}
) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(
                  paymentMethod
              )}`;

    return request(
        `/transactions/analytics/ai-insight${query}`,
        options
    );
}

export { API };