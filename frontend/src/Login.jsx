import { useState } from "react";
import { useAuth } from "./AuthContext";

export default function Login({ onRegister }) {
    const { login } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setLoading(true);

        try {
            await login(email.trim(), password);
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-card">
                <div className="auth-brand">
                    <div className="auth-logo">C</div>

                    <div>
                        <h1>CFOx</h1>
                        <p>Financial Intelligence</p>
                    </div>
                </div>

                <div className="auth-heading">
                    <h2>Welcome back</h2>

                    <p>
                        Sign in to continue to your
                        financial dashboard.
                    </p>
                </div>

                {error && (
                    <div className="auth-error">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <label>
                        Email
                    </label>

                    <input
                        type="email"
                        value={email}
                        onChange={(event) =>
                            setEmail(event.target.value)
                        }
                        placeholder="you@example.com"
                        required
                        autoComplete="email"
                    />

                    <label>
                        Password
                    </label>

                    <input
                        type="password"
                        value={password}
                        onChange={(event) =>
                            setPassword(event.target.value)
                        }
                        placeholder="Your password"
                        required
                        autoComplete="current-password"
                    />

                    <button
                        type="submit"
                        disabled={loading}
                    >
                        {loading
                            ? "Signing in..."
                            : "Sign in"}
                    </button>
                </form>

                <div className="auth-switch">
                    <span>
                        Don't have an account?
                    </span>

                    <button
                        type="button"
                        onClick={onRegister}
                    >
                        Create account
                    </button>
                </div>
            </div>
        </div>
    );
}