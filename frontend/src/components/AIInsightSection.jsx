import AIInsight from "./AIInsight";

function AIInsightSection({
    aiLoading,
    aiInsight,
    loadAIInsight,
}) {
    return (
        <section
            style={{
                background:
                    "rgba(255,255,255,0.04)",
                border:
                    "1px solid rgba(255,255,255,0.08)",
                borderRadius: "16px",
                padding: "24px",
                marginBottom: "24px",
            }}
        >
            <div
                style={{
                    display: "flex",
                    justifyContent:
                        "space-between",
                    alignItems: "center",
                    marginBottom:
                        "16px",
                }}
            >
                <h2
                    style={{
                        margin: 0,
                    }}
                >
                    AI Financial Insight
                </h2>

                <button
                    onClick={() => loadAIInsight()}
                    disabled={aiLoading}
                >
                    {aiLoading
                        ? "Analyzing..."
                        : aiInsight
                          ? "Refresh Insight"
                          : "Generate AI Insight"}
                </button>
            </div>

            {!aiInsight &&
                !aiLoading && (
                    <p
                        style={{
                            opacity: 0.5,
                            margin: 0,
                        }}
                    >
                        Generate an AI-powered
                        financial assessment.
                    </p>
                )}

            {aiLoading && (
                <p
                    style={{
                        opacity: 0.5,
                        margin: 0,
                    }}
                >
                    CFOx is analyzing your
                    financial data...
                </p>
            )}

            {aiInsight && (
                <AIInsight
                    insight={aiInsight}
                />
            )}
        </section>
    );
}

export default AIInsightSection;