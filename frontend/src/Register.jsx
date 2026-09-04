import {useState} from "react";
import {useAuth} from "./AuthContext";

export default function Register({onLogin}) {
    const {register, login} = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] =
        useState("");

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    function validatePassword(value) {
        if (value.length < 12) {
            return "Password must be at least 12 characters.";
        }

        if (!/[a-z]/.test(value)) {
            return "Password must contain at least one lowercase letter.";
        }

        if (!/[A-Z]/.test(value)) {
            return "Password must contain at least one uppercase letter.";
        }

        if (!/[0-9]/.test(value)) {
            return "Password must contain at least one number.";
        }

        if (value.trim() !== value) {
            return "Password must not start or end with whitespace.";
        }

        return "";
    }

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");

        if (password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        const passwordError = validatePassword(password);

        if (passwordError) {
            setError(passwordError);
            return;
        }

        setLoading(true);

        try {
            await register(
                email.trim(),
                password
            );

            await login(
                email.trim(),
                password
            );
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
                    <h2>Create your account</h2>

                    <p>
                        Start analyzing your financial
                        data with CFOx.
                    </p>
                </div>

                {error && (
                    <div className="auth-error">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <label>Email</label>

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

                    <label>Password</label>

                    <input
                        type="password"
                        value={password}
                        onChange={(event) =>
                            setPassword(event.target.value)
                        }
                        placeholder="At least 12 characters"
                        required
                        autoComplete="new-password"
                    />

                    <label>Confirm password</label>

                    <input
                        type="password"
                        value={confirmPassword}
                        onChange={(event) =>
                            setConfirmPassword(
                                event.target.value
                            )
                        }
                        placeholder="Repeat your password"
                        required
                        autoComplete="new-password"
                    />

                    <button
                        type="submit"
                        disabled={loading}
                    >
                        {loading
                            ? "Creating account..."
                            : "Create account"}
                    </button>
                </form>

                <div className="auth-switch">
                    <span>Already have an account?</span>

                    <button
                        type="button"
                        onClick={onLogin}
                    >
                        Sign in
                    </button>
                </div>
            </div>
        </div>
    );
}