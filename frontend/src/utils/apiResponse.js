export async function parseApiResponse(
    response,
    errorMessage
) {
    if (!response.ok) {
        throw new Error(
            `${errorMessage}: ${response.status}`
        );
    }

    return response.json();
}