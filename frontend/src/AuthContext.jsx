import {createContext, useContext, useEffect, useState} from "react";

const API = "http://127.0.0.1:8000";

const AuthContext = createContext(null);

export function AuthProvider({children}) {
    const [token, setToken] = useState(
        () => localStorage.getItem("cfox_access_token")
    );

    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!token) {
            setUser(null);
            setLoading(false);
            return;
        }

        async function loadUser() {
            try {
                const response = await fetch(`${API}/auth/me`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error("Invalid or expired token");
                }

                const data = await response.json();
                setUser(data);
            } catch (error) {
                console.error("Authentication error:", error);

                localStorage.removeItem("cfox_access_token");
                setToken(null);
                setUser(null);
            } finally {
                setLoading(false);
            }
        }

        loadUser();
    }, [token]);

    async function login(email, password) {
        const body = new URLSearchParams();
        body.set("username", email);
        body.set("password", password);

        const response = await fetch(`${API}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data?.detail || "Unable to login"
            );
        }

        const accessToken = data.access_token;

        if (!accessToken) {
            throw new Error("Login response did not contain an access token");
        }

        localStorage.setItem(
            "cfox_access_token",
            accessToken
        );

        setToken(accessToken);

        return accessToken;
    }

    async function register(email, password) {
        const response = await fetch(`${API}/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                email,
                password,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data?.detail || "Unable to register"
            );
        }

        return data;
    }

    function logout() {
        localStorage.removeItem("cfox_access_token");
        setToken(null);
        setUser(null);
    }

    function authFetch(url, options = {}) {
        const headers = new Headers(
            options.headers || {}
        );

        if (token) {
            headers.set(
                "Authorization",
                `Bearer ${token}`
            );
        }

        return fetch(url, {
            ...options,
            headers,
        });
    }

    return (
        <AuthContext.Provider
            value={{
                token,
                user,
                loading,
                login,
                register,
                logout,
                authFetch,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error(
            "useAuth must be used inside AuthProvider"
        );
    }

    return context;
}