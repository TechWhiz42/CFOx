function ActionCenter({
                          alerts,
                          financialActions,
                          paymentMethod,
                          onInvestigate,
                          chatLoading,
                      }) {
    const primaryAlerts = Array.isArray(
        alerts?.primary_alerts
    )
        ? alerts.primary_alerts
        : [];

    const healthActions = Array.isArray(
        financialActions?.actions
    )
        ? financialActions.actions
        : [];

    const priorityForAlert = (alert) => {
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
        P3: 3,
    };

    /*
     * Convert existing alerts into the same internal action shape
     * used by the Financial Action Engine.
     */
    const alertActions = primaryAlerts.map(
        (alert) => ({
            ...alert,
            source: "alert",
            priority:
                priorityForAlert(alert),
            action:
            alert.recommended_action,
            description:
            alert.message,
        })
    );

    /*
     * Financial actions already contain:
     * id
     * priority
     * severity
     * title
     * description
     * metric
     * value
     * action
     * evidence
     */
    const deterministicActions =
        healthActions.map(
            (action) => ({
                ...action,
                source:
                    "financial_health",
            })
        );

    /*
     * Merge both systems.
     *
     * Financial-health actions are preferred when an equivalent
     * alert already exists because they contain structured evidence.
     */
    const merged = [];

    const seenKeys = new Set();

    const normalizeKey = (item) => {
        const id = String(
            item.id || ""
        )
            .toLowerCase()
            .trim();

        const title = String(
            item.title || ""
        )
            .toLowerCase()
            .trim();

        const action = String(
            item.action ||
            item.recommended_action ||
            ""
        )
            .toLowerCase()
            .trim();

        /*
         * Normalize common alert/action equivalents.
         */
        if (
            id.includes("revenue") ||
            title.includes("revenue") ||
            action.includes("revenue")
        ) {
            return "revenue";
        }

        if (
            id.includes("payment") ||
            title.includes("payment") ||
            action.includes("payment")
        ) {
            return "payment";
        }

        if (
            id.includes("cashflow") ||
            id.includes("cash-flow") ||
            title.includes("cash flow") ||
            title.includes("cash-flow") ||
            action.includes("cash-flow")
        ) {
            return "cashflow";
        }

        if (
            id.includes("anomal") ||
            title.includes("anomal") ||
            action.includes("anomal")
        ) {
            return "anomaly";
        }

        return `${id}|${title}|${action}`;
    };

    /*
     * Add deterministic Financial Health actions first.
     */
    deterministicActions.forEach(
        (action) => {
            const key =
                normalizeKey(action);

            if (
                !seenKeys.has(key)
            ) {
                seenKeys.add(key);
                merged.push(action);
            }
        }
    );

    /*
     * Add legacy alerts only when they don't represent an
     * already-present Financial Health action.
     */
    alertActions.forEach(
        (alert) => {
            const key =
                normalizeKey(alert);

            if (
                !seenKeys.has(key)
            ) {
                seenKeys.add(key);
                merged.push(alert);
            }
        }
    );

    const actions = merged.sort(
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

    /*
     * Don't render an empty Action Center.
     */
    if (actions.length === 0) {
        return null;
    }

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
                    alignItems:
                        "flex-start",
                    gap: "16px",
                    marginBottom:
                        "20px",
                    flexWrap: "wrap",
                }}
            >
                <div>
                    <h2
                        style={{
                            margin: 0,
                        }}
                    >
                        Action Center
                    </h2>

                    <p
                        style={{
                            margin:
                                "6px 0 0",
                            opacity: 0.5,
                            fontSize:
                                "13px",
                        }}
                    >
                        Prioritized actions from
                        verified financial intelligence
                        · {methodLabel}
                    </p>
                </div>

                <div
                    style={{
                        display:
                            "flex",
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

                    <PriorityBadge
                        priority="P2"
                        count={
                            actions.filter(
                                (item) =>
                                    item.priority ===
                                    "P2"
                            ).length
                        }
                    />
                </div>
            </div>

            <div
                style={{
                    display:
                        "grid",
                    gap: "10px",
                }}
            >
                {actions.map(
                    (item) => {
                        const isHealthAction =
                            item.source ===
                            "financial_health";

                        return (
                            <div
                                key={`${item.source}-${item.id}`}
                                style={{
                                    display:
                                        "grid",
                                    gridTemplateColumns:
                                        "52px minmax(0, 1fr) auto",
                                    gap:
                                        "16px",
                                    alignItems:
                                        "center",
                                    padding:
                                        "17px",
                                    borderRadius:
                                        "13px",
                                    background:
                                        "rgba(255,255,255,0.025)",
                                    border:
                                        "1px solid rgba(255,255,255,0.06)",
                                }}
                            >
                                <PriorityBadge
                                    priority={
                                        item.priority
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
                                            display:
                                                "flex",
                                            alignItems:
                                                "center",
                                            gap:
                                                "9px",
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
                                                item.title
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
                                                item.severity
                                            }
                                        </span>

                                        {isHealthAction && (
                                            <span
                                                style={{
                                                    fontSize:
                                                        "10px",
                                                    textTransform:
                                                        "uppercase",
                                                    letterSpacing:
                                                        "0.04em",
                                                    opacity:
                                                        0.55,
                                                }}
                                            >
                                                Health
                                                signal
                                            </span>
                                        )}
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
                                            item.description
                                        }
                                    </p>

                                    {isHealthAction &&
                                        item.metric && (
                                            <div
                                                style={{
                                                    fontSize:
                                                        "11px",
                                                    opacity:
                                                        0.75,
                                                    marginTop:
                                                        "6px",
                                                }}
                                            >
                                                <span
                                                    style={{
                                                        opacity:
                                                            0.45,
                                                    }}
                                                >
                                                    Metric:{" "}
                                                </span>

                                                {
                                                    item.metric
                                                }

                                                {item.value !==
                                                    undefined &&
                                                    item.value !==
                                                    null && (
                                                        <>
                                                            {" "}
                                                            ·{" "}
                                                            <strong>
                                                                {
                                                                    item.value
                                                                }
                                                            </strong>
                                                        </>
                                                    )}
                                            </div>
                                        )}

                                    <div
                                        style={{
                                            fontSize:
                                                "11px",
                                            opacity:
                                                0.8,
                                            marginTop:
                                                "5px",
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
                                            item.action
                                        }
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    onClick={() =>
                                        onInvestigate(
                                            item
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
                        );
                    }
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

    const background =
        isP0
            ? "rgba(251,113,133,0.10)"
            : isP1
                ? "rgba(251,191,36,0.10)"
                : "rgba(255,255,255,0.07)";

    const color =
        isP0
            ? "#fb7185"
            : isP1
                ? "#fbbf24"
                : "#a1a1aa";

    return (
        <div
            style={{
                display:
                    "inline-flex",
                alignItems:
                    "center",
                justifyContent:
                    "center",
                gap:
                    count !== undefined
                        ? "6px"
                        : undefined,
                minWidth:
                    compact
                        ? "42px"
                        : undefined,
                padding:
                    compact
                        ? "7px 8px"
                        : "6px 9px",
                borderRadius:
                    "8px",
                background,
                color,
                fontSize:
                    "10px",
                fontWeight:
                    800,
                letterSpacing:
                    "0.04em",
            }}
        >
            {priority}

            {count !==
                undefined && (
                    <span
                        style={{
                            opacity:
                                0.75,
                        }}
                    >
                    {count}
                </span>
                )}
        </div>
    );
}


export default ActionCenter;