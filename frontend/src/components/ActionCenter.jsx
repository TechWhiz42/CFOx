function ActionCenter({
    alerts,
    paymentMethod,
    onInvestigate,
    chatLoading,
}) {
    const primaryAlerts = Array.isArray(
        alerts?.primary_alerts
    )
        ? alerts.primary_alerts
        : [];

    if (primaryAlerts.length === 0) {
        return null;
    }

    const priorityFor = (alert) => {
        if (
            alert.severity ===
            "critical"
        ) {
            return "P0";
        }

        if (
            alert.severity ===
            "warning"
        ) {
            return "P1";
        }

        return "P2";
    };

    const priorityRank = {
        P0: 0,
        P1: 1,
        P2: 2,
    };

    const actions = [...primaryAlerts]
        .map((alert) => ({
            ...alert,
            priority:
                priorityFor(alert),
        }))
        .sort(
            (a, b) =>
                priorityRank[
                    a.priority
                ] -
                priorityRank[
                    b.priority
                ]
        );

    const methodLabel =
        paymentMethod === "all"
            ? "All payment methods"
            : paymentMethod.toUpperCase();

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
                    alignItems: "flex-start",
                    gap: "16px",
                    marginBottom: "20px",
                    flexWrap: "wrap",
                }}
            >
                <div>
                    <h2 style={{ margin: 0 }}>
                        Action Center
                    </h2>

                    <p
                        style={{
                            margin: "6px 0 0",
                            opacity: 0.5,
                            fontSize: "13px",
                        }}
                    >
                        Prioritized actions from verified financial
                        alerts · {methodLabel}
                    </p>
                </div>

                <div
                    style={{
                        display: "flex",
                        gap: "8px",
                    }}
                >
                    <PriorityBadge
                        priority="P0"
                        count={
                            actions.filter(
                                (item) =>
                                    item.priority ===
                                    "P0"
                            ).length
                        }
                    />

                    <PriorityBadge
                        priority="P1"
                        count={
                            actions.filter(
                                (item) =>
                                    item.priority ===
                                    "P1"
                            ).length
                        }
                    />
                </div>
            </div>

            <div
                style={{
                    display: "grid",
                    gap: "10px",
                }}
            >
                {actions.map(
                    (alert) => (
                        <div
                            key={alert.id}
                            style={{
                                display: "grid",
                                gridTemplateColumns:
                                    "52px minmax(0, 1fr) auto",
                                gap: "16px",
                                alignItems: "center",
                                padding: "17px",
                                borderRadius: "13px",
                                background:
                                    "rgba(255,255,255,0.025)",
                                border:
                                    "1px solid rgba(255,255,255,0.06)",
                            }}
                        >
                            <PriorityBadge
                                priority={
                                    alert.priority
                                }
                                compact
                            />

                            <div
                                style={{
                                    minWidth: 0,
                                }}
                            >
                                <div
                                    style={{
                                        display: "flex",
                                        alignItems:
                                            "center",
                                        gap: "9px",
                                        flexWrap:
                                            "wrap",
                                    }}
                                >
                                    <strong
                                        style={{
                                            fontSize:
                                                "14px",
                                        }}
                                    >
                                        {
                                            alert.title
                                        }
                                    </strong>

                                    <span
                                        style={{
                                            fontSize:
                                                "10px",
                                            textTransform:
                                                "uppercase",
                                            opacity:
                                                0.45,
                                        }}
                                    >
                                        {
                                            alert.severity
                                        }
                                    </span>
                                </div>

                                <p
                                    style={{
                                        margin:
                                            "5px 0",
                                        fontSize:
                                            "12px",
                                        lineHeight:
                                            1.45,
                                        opacity:
                                            0.6,
                                    }}
                                >
                                    {
                                        alert.message
                                    }
                                </p>

                                <div
                                    style={{
                                        fontSize:
                                            "11px",
                                        opacity:
                                            0.8,
                                    }}
                                >
                                    <span
                                        style={{
                                            opacity:
                                                0.45,
                                        }}
                                    >
                                        Next action:{" "}
                                    </span>
                                    {
                                        alert.recommended_action
                                    }
                                </div>
                            </div>

                            <button
                                type="button"
                                onClick={() =>
                                    onInvestigate(
                                        alert
                                    )
                                }
                                disabled={
                                    chatLoading
                                }
                                style={{
                                    whiteSpace:
                                        "nowrap",
                                    padding:
                                        "9px 12px",
                                    borderRadius:
                                        "9px",
                                    border:
                                        "1px solid rgba(139,92,246,0.28)",
                                    background:
                                        "rgba(139,92,246,0.10)",
                                    color:
                                        "#c4b5fd",
                                    fontSize:
                                        "11px",
                                    fontWeight:
                                        700,
                                    cursor:
                                        chatLoading
                                            ? "not-allowed"
                                            : "pointer",
                                }}
                            >
                                Investigate
                            </button>
                        </div>
                    )
                )}
            </div>
        </section>
    );
}

function PriorityBadge({
    priority,
    count,
    compact = false,
}) {
    const isP0 =
        priority === "P0";
    const isP1 =
        priority === "P1";

    const background = isP0
        ? "rgba(251,113,133,0.10)"
        : isP1
          ? "rgba(251,191,36,0.10)"
          : "rgba(255,255,255,0.07)";

    const color = isP0
        ? "#fb7185"
        : isP1
          ? "#fbbf24"
          : "#a1a1aa";

    return (
        <div
            style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap:
                    count !== undefined
                        ? "6px"
                        : undefined,
                minWidth: compact
                    ? "42px"
                    : undefined,
                padding: compact
                    ? "7px 8px"
                    : "6px 9px",
                borderRadius: "8px",
                background,
                color,
                fontSize: "10px",
                fontWeight: 800,
                letterSpacing: "0.04em",
            }}
        >
            {priority}

            {count !== undefined && (
                <span
                    style={{
                        opacity: 0.75,
                    }}
                >
                    {count}
                </span>
            )}
        </div>
    );
}

export default ActionCenter;