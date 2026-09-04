export class ApiError extends Error {
    constructor(
        message,
        {
            status = null,
            code = null,
            requestId = null,
            details = null,
        } = {}
    ) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.code = code;
        this.requestId = requestId;
        this.details = details;
    }
}


export async function parseApiResponse(
    response,
    fallbackMessage = "Request failed"
) {
    let data = null;

    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok) {
        throw new ApiError(
            data?.message ||
                data?.detail ||
                `${fallbackMessage}: ${response.status}`,
            {
                status: response.status,
                code: data?.error || null,
                requestId:
                    data?.request_id ||
                    response.headers.get("X-Request-ID") ||
                    null,
                details: data,
            }
        );
    }

    return data;
}


export function getApiErrorMessage(
    error,
    fallbackMessage = "Something went wrong."
) {
    if (error instanceof ApiError) {
        return error.message;
    }

    if (error instanceof Error && error.message) {
        return error.message;
    }

    return fallbackMessage;
}