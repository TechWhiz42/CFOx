function Header({
                    paymentMethod,
                    setPaymentMethod,
                    loading,
                    chatLoading,
                    theme,
                    setTheme,
                    user,
                    onLogout,
                }) {
    const disabled = loading || chatLoading;

    return (
        <header className="cfox-header">
            <div className="cfox-header-inner">
                <div className="cfox-brand">
                    <div className="cfox-brand-mark">C</div>
                    <div>
                        <div className="cfox-brand-name">CFOx</div>
                        <div className="cfox-brand-subtitle">
                            AI Financial Controller
                        </div>
                    </div>
                </div>

                <div className="cfox-header-actions">
                    <label
                        className="cfox-filter-label"
                        htmlFor="payment-method-selector"
                    >
                        Payment method
                    </label>

                    <select
                        className="cfox-select"
                        id="payment-method-selector"
                        value={paymentMethod}
                        onChange={(event) =>
                            setPaymentMethod(
                                event.target.value
                            )
                        }
                        disabled={disabled}
                    >
                        <option value="all">All methods</option>
                        <option value="upi">UPI</option>
                        <option value="card">Card</option>
                        <option value="netbanking">
                            Netbanking
                        </option>
                    </select>

                    {user && (
                        <div className="cfox-account">
                            <div className="cfox-account-avatar" aria-hidden="true">
                                {(user.email || "U").charAt(0).toUpperCase()}
                            </div>
                            <div className="cfox-account-copy">
                                <span className="cfox-account-label">SIGNED IN</span>
                                <span className="cfox-account-email">{user.email}</span>
                            </div>
                            <button
                                type="button"
                                className="cfox-signout"
                                onClick={onLogout}
                                disabled={chatLoading}
                            >
                                Sign out
                            </button>
                        </div>
                    )}

                    <div className="cfox-system-status">
                        <span className="cfox-status-dot"/>
                        System operational
                    </div>

                    <div
                        className="cfox-theme-control"
                        aria-label="Theme"
                    >
                        {[
                            ["system", "System"],
                            ["light", "Light"],
                            ["dark", "Dark"],
                        ].map(([value, label]) => (
                            <button
                                key={value}
                                type="button"
                                className={
                                    theme === value
                                        ? "is-active"
                                        : ""
                                }
                                onClick={() =>
                                    setTheme(value)
                                }
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Header;
