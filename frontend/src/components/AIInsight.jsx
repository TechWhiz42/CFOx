function AIInsight({
    insight,
}) {
    if (
        typeof insight ===
        "string"
    ) {
        return (
            <div
                style={{
                    whiteSpace:
                        "pre-wrap",
                    lineHeight:
                        1.7,
                    opacity:
                        0.9,
                }}
            >
                {insight}
            </div>
        );
    }

    return (
        <div>
            {insight.summary && (
                <div
                    style={{
                        marginBottom:
                            "18px",
                    }}
                >
                    <strong>
                        Summary
                    </strong>

                    <p
                        style={{
                            lineHeight:
                                1.6,
                        }}
                    >
                        {
                            insight.summary
                        }
                    </p>
                </div>
            )}

            {insight.severity && (
                <div
                    style={{
                        marginBottom:
                            "18px",
                    }}
                >
                    <strong>
                        Severity
                    </strong>

                    <p
                        style={{
                            textTransform:
                                "capitalize",
                        }}
                    >
                        {
                            insight.severity
                        }
                    </p>
                </div>
            )}

            {Array.isArray(
                insight.evidence
            ) &&
                insight.evidence
                    .length >
                    0 && (
                    <div
                        style={{
                            marginBottom:
                                "18px",
                        }}
                    >
                        <strong>
                            Evidence
                        </strong>

                        <ul>
                            {insight.evidence.map(
                                (
                                    item,
                                    index
                                ) => (
                                    <li
                                        key={
                                            index
                                        }
                                    >
                                        {
                                            item
                                        }
                                    </li>
                                )
                            )}
                        </ul>
                    </div>
                )}

            {insight.impact && (
                <div
                    style={{
                        marginBottom:
                            "18px",
                    }}
                >
                    <strong>
                        Impact
                    </strong>

                    <p
                        style={{
                            lineHeight:
                                1.6,
                        }}
                    >
                        {
                            insight.impact
                        }
                    </p>
                </div>
            )}

            {Array.isArray(
                insight.recommendations
            ) &&
                insight
                    .recommendations
                    .length >
                    0 && (
                    <div>
                        <strong>
                            Recommendations
                        </strong>

                        <ol>
                            {insight.recommendations.map(
                                (
                                    item,
                                    index
                                ) => (
                                    <li
                                        key={
                                            index
                                        }
                                    >
                                        {
                                            item
                                        }
                                    </li>
                                )
                            )}
                        </ol>
                    </div>
                )}
        </div>
    );
}


/*
 * =========================================================
 * SEVERITY BADGE
 * =========================================================
 */

export default AIInsight;