export function buildVerifiedEvidence(evidence) {
    const verifiedEvidence = {};

    if (!Array.isArray(evidence)) {
        return verifiedEvidence;
    }

    evidence.forEach((item) => {
        if (
            item?.label &&
            item?.value !== undefined
        ) {
            verifiedEvidence[item.label] =
                item.value;
        }
    });

    return verifiedEvidence;
}

export function getPaymentMethodLabel(
    paymentMethod
) {
    return paymentMethod === "all"
        ? "all payment methods"
        : paymentMethod;
}