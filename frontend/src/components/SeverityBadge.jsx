function SeverityBadge({
                           severity,
                       }) {
    const normalized =
        String(
            severity ||
            "normal"
        ).toLowerCase();

    let background =
        "rgba(34,197,94,0.12)";

    let color =
        "#4ade80";

    if (
        normalized ===
        "warning" ||
        normalized === "high"
    ) {
        background =
            "rgba(234,179,8,0.12)";
        color =
            "#facc15";
    }

    if (
        normalized ===
        "critical"
    ) {
        background =
            "rgba(239,68,68,0.12)";
        color =
            "#f87171";
    }

    return (
        <span
            style={{
                padding:
                    "7px 12px",
                borderRadius:
                    "999px",
                background,
                color,
                fontSize:
                    "12px",
                fontWeight:
                    700,
                textTransform:
                    "uppercase",
            }}
        >
            {normalized}
        </span>
    );
}


/*
 * =========================================================
 * METRIC CARD
 * =========================================================
 */

export default SeverityBadge;