import {useEffect, useState} from "react";
import {createTransaction, getTransactions} from "../api/transactions";

const PAGE_SIZE = 20;

const EMPTY_FORM = {
    razorpay_payment_id: "",
    amount: "",
    currency: "INR",
    status: "success",
    payment_method: "upi",
    customer_id: "",
    created_at: "",
};

function formatAmount(amount, currency = "INR") {
    const value = Number(amount);
    if (!Number.isFinite(value)) return `${currency} ${amount ?? "0"}`;

    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency,
        maximumFractionDigits: 2,
    }).format(value);
}

function formatDate(value) {
    if (!value) return "—";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;

    return new Intl.DateTimeFormat("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
}

function getErrorMessage(response, fallback) {
    return response
        .json()
        .then((data) => {
            if (typeof data?.detail === "string") return data.detail;
            if (Array.isArray(data?.detail)) {
                return data.detail
                    .map((item) => item?.msg)
                    .filter(Boolean)
                    .join("; ");
            }
            return fallback;
        })
        .catch(() => fallback);
}

function statusClass(status) {
    return `cfox-transaction-status cfox-transaction-status-${String(
        status || "unknown"
    ).toLowerCase()}`;
}

function TransactionManager({authFetch, onDataChanged}) {
    const [transactions, setTransactions] = useState([]);
    const [offset, setOffset] = useState(0);
    const [hasNext, setHasNext] = useState(false);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState(EMPTY_FORM);

    async function loadTransactions(nextOffset = offset) {
        setLoading(true);
        setError("");

        try {
            const response = await getTransactions(
                {
                    limit: PAGE_SIZE,
                    offset: nextOffset,
                },
                authFetch
            );

            if (response.status === 401) {
                throw new Error("Your session has expired. Please sign in again.");
            }

            if (!response.ok) {
                throw new Error(
                    await getErrorMessage(
                        response,
                        "Unable to load transactions."
                    )
                );
            }

            const data = await response.json();
            const rows = Array.isArray(data)
                ? data
                : data?.transactions || data?.items || [];

            setTransactions(rows);
            setOffset(nextOffset);
            setHasNext(rows.length === PAGE_SIZE);
        } catch (err) {
            if (err?.name !== "AbortError") {
                setError(err?.message || "Unable to load transactions.");
            }
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadTransactions(0);
        // authFetch is stable for the lifetime of a logged-in session.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    function updateField(name, value) {
        setForm((previous) => ({
            ...previous,
            [name]: value,
        }));
    }

    async function handleSubmit(event) {
        event.preventDefault();
        setError("");
        setNotice("");

        const amount = Number(form.amount);
        if (!form.razorpay_payment_id.trim()) {
            setError("Razorpay payment ID is required.");
            return;
        }
        if (!Number.isFinite(amount) || amount <= 0) {
            setError("Amount must be greater than zero.");
            return;
        }

        setSubmitting(true);

        try {
            const payload = {
                razorpay_payment_id: form.razorpay_payment_id.trim(),
                amount: form.amount,
                currency: "INR",
                status: form.status,
                payment_method: form.payment_method || null,
                customer_id: form.customer_id.trim() || null,
            };

            if (form.created_at) {
                payload.created_at = new Date(form.created_at).toISOString();
            }

            const response = await createTransaction(payload, authFetch);

            if (response.status === 401) {
                throw new Error("Your session has expired. Please sign in again.");
            }

            if (!response.ok) {
                throw new Error(
                    await getErrorMessage(
                        response,
                        "Unable to create transaction."
                    )
                );
            }

            setForm(EMPTY_FORM);
            setShowForm(false);
            setNotice("Transaction created successfully.");
            await loadTransactions(0);
            await onDataChanged?.();
        } catch (err) {
            setError(err?.message || "Unable to create transaction.");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <section className="cfox-transactions">
            <div className="cfox-transaction-heading">
                <div>
                    <div className="cfox-section-kicker">TRANSACTION CONTROL</div>
                    <h2>Transactions</h2>
                    <p>
                        Review recent payments and add verified transaction records.
                    </p>
                </div>

                <button
                    type="button"
                    className="cfox-primary-button"
                    onClick={() => {
                        setShowForm((value) => !value);
                        setError("");
                        setNotice("");
                    }}
                    disabled={submitting}
                >
                    {showForm ? "Close form" : "+ Add transaction"}
                </button>
            </div>

            {showForm && (
                <form className="cfox-transaction-form" onSubmit={handleSubmit}>
                    <div className="cfox-form-grid">
                        <label>
                            <span>Razorpay payment ID *</span>
                            <input
                                value={form.razorpay_payment_id}
                                onChange={(event) =>
                                    updateField("razorpay_payment_id", event.target.value)
                                }
                                placeholder="pay_..."
                                maxLength={255}
                                required
                            />
                        </label>

                        <label>
                            <span>Amount (INR) *</span>
                            <input
                                type="number"
                                min="0.01"
                                step="0.01"
                                value={form.amount}
                                onChange={(event) => updateField("amount", event.target.value)}
                                placeholder="1499.50"
                                required
                            />
                        </label>

                        <label>
                            <span>Status *</span>
                            <select
                                value={form.status}
                                onChange={(event) => updateField("status", event.target.value)}
                            >
                                <option value="success">Success</option>
                                <option value="failed">Failed</option>
                                <option value="refunded">Refunded</option>
                            </select>
                        </label>

                        <label>
                            <span>Payment method</span>
                            <select
                                value={form.payment_method}
                                onChange={(event) =>
                                    updateField("payment_method", event.target.value)
                                }
                            >
                                <option value="upi">UPI</option>
                                <option value="card">Card</option>
                                <option value="netbanking">Netbanking</option>
                            </select>
                        </label>

                        <label>
                            <span>Customer ID</span>
                            <input
                                value={form.customer_id}
                                onChange={(event) => updateField("customer_id", event.target.value)}
                                placeholder="customer_123"
                                maxLength={255}
                            />
                        </label>

                        <label>
                            <span>Transaction time</span>
                            <input
                                type="datetime-local"
                                value={form.created_at}
                                onChange={(event) => updateField("created_at", event.target.value)}
                            />
                        </label>
                    </div>

                    <div className="cfox-form-footer">
                        <span className="cfox-form-helper">
                            Ownership is assigned automatically from your signed-in account.
                        </span>
                        <button
                            type="submit"
                            className="cfox-primary-button"
                            disabled={submitting}
                        >
                            {submitting ? "Creating…" : "Create transaction"}
                        </button>
                    </div>
                </form>
            )}

            {notice && <div className="cfox-transaction-notice">{notice}</div>}
            {error && (
                <div className="cfox-transaction-error" role="alert">
                    {error}
                </div>
            )}

            <div className="cfox-transaction-table-wrap">
                {loading ? (
                    <div className="cfox-transaction-state">
                        <div className="cfox-table-skeleton"/>
                        <div className="cfox-table-skeleton"/>
                        <div className="cfox-table-skeleton"/>
                    </div>
                ) : transactions.length === 0 ? (
                    <div className="cfox-transaction-empty">
                        <div className="cfox-empty-icon">₹</div>
                        <h3>No transactions yet</h3>
                        <p>
                            Add your first payment record to start tracking it in CFOx.
                        </p>
                        <button
                            type="button"
                            className="cfox-secondary-button"
                            onClick={() => setShowForm(true)}
                        >
                            Add your first transaction
                        </button>
                    </div>
                ) : (
                    <table className="cfox-transaction-table">
                        <thead>
                        <tr>
                            <th>Payment</th>
                            <th>Customer</th>
                            <th>Amount</th>
                            <th>Status</th>
                            <th>Method</th>
                            <th>Created</th>
                        </tr>
                        </thead>
                        <tbody>
                        {transactions.map((transaction) => (
                            <tr key={transaction.id || transaction.razorpay_payment_id}>
                                <td>
                                    <strong>{transaction.razorpay_payment_id}</strong>
                                    <span>#{transaction.id}</span>
                                </td>
                                <td>{transaction.customer_id || "—"}</td>
                                <td className="cfox-amount-cell">
                                    {formatAmount(
                                        transaction.amount,
                                        transaction.currency || "INR"
                                    )}
                                </td>
                                <td>
                                        <span className={statusClass(transaction.status)}>
                                            {transaction.status || "unknown"}
                                        </span>
                                </td>
                                <td>
                                    {transaction.payment_method
                                        ? transaction.payment_method.toUpperCase()
                                        : "—"}
                                </td>
                                <td>{formatDate(transaction.created_at)}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                )}
            </div>

            <div className="cfox-pagination">
                <span>
                    Showing {transactions.length ? offset + 1 : 0}–
                    {offset + transactions.length}
                </span>
                <div>
                    <button
                        type="button"
                        className="cfox-secondary-button"
                        onClick={() => loadTransactions(Math.max(0, offset - PAGE_SIZE))}
                        disabled={loading || offset === 0}
                    >
                        Previous
                    </button>
                    <button
                        type="button"
                        className="cfox-secondary-button"
                        onClick={() => loadTransactions(offset + PAGE_SIZE)}
                        disabled={loading || !hasNext}
                    >
                        Next
                    </button>
                </div>
            </div>
        </section>
    );
}

export default TransactionManager;
