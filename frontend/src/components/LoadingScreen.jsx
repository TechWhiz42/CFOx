function LoadingScreen() {
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
                <div
                    style={{
                        fontSize: "32px",
                        fontWeight: 700,
                        marginBottom: "12px",
                    }}
                >
                    CFOx
                </div>

                <div
                    style={{
                        opacity: 0.6,
                    }}
                >
                    Loading financial data...
                </div>
            </div>
        </div>
    );
}

export default LoadingScreen;