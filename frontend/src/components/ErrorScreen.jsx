function ErrorScreen({
    error,
    onRetry,
}) {
    return (
        <div
            style={{
                minHeight: "100vh",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "#0b0f19",
                color: "#ffffff",
                fontFamily:
                    "Inter, system-ui, sans-serif",
            }}
        >
            <div
                style={{
                    textAlign: "center",
                }}
            >
                <h2>
                    CFOx couldn't connect
                </h2>

                <p
                    style={{
                        opacity: 0.6,
                    }}
                >
                    {error}
                </p>

                <button
                    onClick={onRetry}
                >
                    Retry
                </button>
            </div>
        </div>
    );
}

export default ErrorScreen;