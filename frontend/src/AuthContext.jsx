import {createContext, useContext, useEffect, useState,} from "react";
import {API} from "./api/config";

const AuthContext = createContext(null);

export function AuthProvider({children}) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    function clearSession() {
        setUser(null);
        setLoading(false);
    }

    useEffect(() => {
        let cancelled = false;

        async function loadUser() {
            try {
                const response = await fetch(
                    `${API}/auth/me`,
                    {
                        method: "GET",
                        credentials: "include",
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data?.detail ||
                        data?.message ||
                        `Authentication failed (${response.status})`
                    );
                }

                if (cancelled) {
                    return;
                }

                setUser(data);
                setLoading(false);
            } catch (error) {
                console.error(
                    "Authentication error:",
                    error
                );

                if (!cancelled) {
                    clearSession();
                }
            }
        }

        loadUser();

        return () => {
            cancelled = true;
        };
    }, []);

    async function login(email, password) {
        const body = new URLSearchParams();

        body.set(
            "username",
            email.trim().toLowerCase()
        );

        body.set("password", password);

        const response = await fetch(
            `${API}/auth/login`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/x-www-form-urlencoded",
                },
                body,
                credentials: "include",
            }
        );

        let data = null;

        try {
            data = await response.json();
        } catch {
            data = null;
        }

        if (!response.ok) {
            throw new Error(
                data?.detail ||
                data?.message ||
                `Unable to login (${response.status})`
            );
        }

        const meResponse = await fetch(
            `${API}/auth/me`,
            {
                method: "GET",
                credentials: "include",
            }
        );

        const meData = await meResponse.json();

        if (!meResponse.ok) {
            clearSession();

            throw new Error(
                meData?.detail ||
                meData?.message ||
                `Unable to verify login (${meResponse.status})`
            );
        }

        setUser(meData);
        setLoading(false);

        return {
            status: "authenticated",
        };
    }

    async function register(email, password) {
        const response = await fetch(
            `${API}/auth/register`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    email: email.trim().toLowerCase(),
                    password,
                }),
                credentials: "include",
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data?.detail ||
                data?.message ||
                `Unable to register (${response.status})`
            );
        }

        return data;
    }

    async function logout() {
        try {
            await fetch(
                `${API}/auth/logout`,
                {
                    method: "POST",
                    credentials: "include",
                }
            );
        } finally {
            clearSession();
        }
    }

    async function authFetch(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            credentials: "include",
            headers: new Headers(options.headers || {}),
        });

        if (response.status === 401) {
            clearSession();
        }

        return response;
    }

    return (
        <AuthContext.Provider
            value={{
                token: user ? "cookie" : null,
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