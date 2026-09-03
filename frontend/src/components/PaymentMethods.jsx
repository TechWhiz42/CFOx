function PaymentMethods({
    paymentMethods,
    paymentMethodsLoading,
    selectedPaymentMethod,

    onSelectPaymentMethod,
    investigatePaymentMethod,
    PaymentMethodDetail,
    chatLoading,
}) {
    return (

            <section
                style={{
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "16px",
                    padding: "24px",
                    marginBottom: "24px",
                }}
            >
                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "20px",
                        gap: "16px",
                        flexWrap: "wrap",
                    }}
                >
                    <div>
                        <h2 style={{ margin: 0 }}>
                            Payment Methods
                        </h2>

                        <p
                            style={{
                                margin: "6px 0 0",
                                opacity: 0.5,
                                fontSize: "13px",
                            }}
                        >
                            Compare payment rails · click a method to
                            drill down
                        </p>
                    </div>

                    {paymentMethods?.worst_performing_method && (
                        <div
                            style={{
                                padding: "8px 12px",
                                borderRadius: "999px",
                                background: "rgba(239,68,68,0.12)",
                                color: "#f87171",
                                fontSize: "13px",
                            }}
                        >
                            Worst:{" "}
                            <strong>
                                {paymentMethods.worst_performing_method.toUpperCase()}
                            </strong>
                        </div>
                    )}
                </div>

                {paymentMethodsLoading ? (
                    <div style={{ opacity: 0.5 }}>
                        Loading payment analytics...
                    </div>
                ) : !paymentMethods ? (
                    <div style={{ opacity: 0.5 }}>
                        Payment analytics unavailable.
                    </div>
                ) : (
                    <>
                        <div
                            style={{
                                display: "grid",
                                gridTemplateColumns:
                                    "repeat(auto-fit, minmax(220px, 1fr))",
                                gap: "16px",
                            }}
                        >
                            {paymentMethods.payment_methods?.map((method) => {
                                const current =
                                    method.current_period || {};

                                const previous =
                                    method.previous_period || {};

                                const failureChange =
                                    method.failure_rate_change ?? 0;

                                const isWorst =
                                    method.payment_method ===
                                    paymentMethods.worst_performing_method;

                                const isSelected =
                                    selectedPaymentMethod?.payment_method ===
                                    method.payment_method;

                                return (
                                    <button
                                        key={method.payment_method}
                                        type="button"
                                        onClick={() =>
                                            setSelectedPaymentMethod(
                                                isSelected ? null : method
                                            )
                                        }
                                        disabled={chatLoading}
                                        style={{
                                            textAlign: "left",
                                            width: "100%",
                                            background: isSelected
                                                ? "rgba(139,92,246,0.12)"
                                                : isWorst
                                                  ? "rgba(239,68,68,0.08)"
                                                  : "rgba(255,255,255,0.03)",
                                            border: isSelected
                                                ? "1px solid rgba(139,92,246,0.42)"
                                                : isWorst
                                                  ? "1px solid rgba(239,68,68,0.25)"
                                                  : "1px solid rgba(255,255,255,0.07)",
                                            borderRadius: "14px",
                                            padding: "18px",
                                            color: "#ffffff",
                                            boxShadow: isSelected
                                                ? "0 0 0 1px rgba(139,92,246,0.08), 0 12px 32px rgba(0,0,0,0.18)"
                                                : "none",
                                            cursor: chatLoading
                                                ? "not-allowed"
                                                : "pointer",
                                        }}
                                    >
                                        <div
                                            style={{
                                                display: "flex",
                                                justifyContent:
                                                    "space-between",
                                                alignItems: "center",
                                                marginBottom: "18px",
                                            }}
                                        >
                                            <strong
                                                style={{
                                                    textTransform: "uppercase",
                                                    letterSpacing: "0.04em",
                                                }}
                                            >
                                                {method.payment_method}
                                            </strong>

                                            <div
                                                style={{
                                                    display: "flex",
                                                    alignItems: "center",
                                                    gap: "8px",
                                                }}
                                            >
                                                {isWorst && (
                                                    <span
                                                        style={{
                                                            fontSize: "11px",
                                                            color: "#f87171",
                                                            fontWeight: 700,
                                                        }}
                                                    >
                                                        WORST
                                                    </span>
                                                )}

                                                <span
                                                    style={{
                                                        fontSize: "11px",
                                                        opacity: 0.4,
                                                    }}
                                                >
                                                    {isSelected
                                                        ? "OPEN"
                                                        : "DETAILS"}
                                                </span>
                                            </div>
                                        </div>

                                        <div
                                            style={{
                                                fontSize: "28px",
                                                fontWeight: 700,
                                                marginBottom: "4px",
                                            }}
                                        >
                                            {current.failure_rate ?? 0}%
                                        </div>

                                        <div
                                            style={{
                                                fontSize: "12px",
                                                opacity: 0.5,
                                                marginBottom: "16px",
                                            }}
                                        >
                                            Current failure rate
                                        </div>

                                        <div
                                            style={{
                                                display: "grid",
                                                gridTemplateColumns: "1fr 1fr",
                                                gap: "12px",
                                            }}
                                        >
                                            <div>
                                                <div
                                                    style={{
                                                        fontSize: "11px",
                                                        opacity: 0.45,
                                                    }}
                                                >
                                                    Previous
                                                </div>

                                                <div
                                                    style={{
                                                        marginTop: "4px",
                                                    }}
                                                >
                                                    {previous.failure_rate ?? 0}%
                                                </div>
                                            </div>

                                            <div>
                                                <div
                                                    style={{
                                                        fontSize: "11px",
                                                        opacity: 0.45,
                                                    }}
                                                >
                                                    Change
                                                </div>

                                                <div
                                                    style={{
                                                        marginTop: "4px",
                                                        color:
                                                            failureChange > 0
                                                                ? "#fb7185"
                                                                : "#34d399",
                                                    }}
                                                >
                                                    {failureChange >= 0
                                                        ? "+"
                                                        : ""}
                                                    {failureChange} pp
                                                </div>
                                            </div>
                                        </div>

                                        <div
                                            style={{
                                                marginTop: "16px",
                                                paddingTop: "12px",
                                                borderTop:
                                                    "1px solid rgba(255,255,255,0.06)",
                                                fontSize: "12px",
                                                opacity: 0.6,
                                            }}
                                        >
                                            {current.total_transactions ?? 0}{" "}
                                            transactions
                                            {" · "}₹
                                            {Number(
                                                current.revenue || 0
                                            ).toLocaleString("en-IN", {
                                                maximumFractionDigits: 0,
                                            })}{" "}
                                            revenue
                                        </div>
                                    </button>
                                );
                            })}
                        </div>

                        {selectedPaymentMethod && (
                            <PaymentMethodDetail
                                method={selectedPaymentMethod}
                                onClose={() =>
                                    onSelectPaymentMethod(null)
                                }
                                onInvestigate={investigatePaymentMethod}
                                chatLoading={chatLoading}
                            />
                        )}
                    </>
                )}
            </section>
    );
}

export default PaymentMethods;