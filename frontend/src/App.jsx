import {useEffect, useRef, useState} from "react";
import {useAuth} from "./AuthContext";
import Login from "./Login";
import Register from "./Register";
import {
    listConversations,
    createConversation,
    getConversation,
    streamConversationMessage,
    deleteConversation,
} from "./api/conversations";

const API =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000";
import {buildVerifiedEvidence, getPaymentMethodLabel} from "./utils/investigation";
import {
    beginRequest,
    isCurrentRequest,
    isSameRequest,
} from "./utils/request";
import {
    QUICK_QUESTIONS,
    TOOL_LABELS,
} from "./utils/constants";
import {parseApiResponse} from "./utils/apiResponse";

import CFOChat from "./components/CFOChat";
import Anomaly from "./components/Anomaly";
import FinancialIntelligence from "./components/FinancialIntelligence";
import Header from "./components/Header";
import KpiCards from "./components/KpiCards";
import PaymentMethods from "./components/PaymentMethods";
import HistoricalTrend from "./components/HistoricalTrend";
import FinancialImpact from "./components/FinancialImpact";
import ActionCenter from "./components/ActionCenter";
import RevenueTrend from "./components/RevenueTrend";
import AIInsightSection from "./components/AIInsightSection";
import TransactionManager from "./components/TransactionManager";
import LoadingScreen from "./components/LoadingScreen";
import ErrorScreen from "./components/ErrorScreen";
import "./styles/cfox-razor-theme.css";

const AUTH_STYLES = `
    .cfox-auth-page {
        min-height: 100vh;
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 32px;
        background:
            radial-gradient(circle at 15% 20%, rgba(47, 102, 255, 0.16), transparent 32%),
            radial-gradient(circle at 88% 80%, rgba(99, 102, 241, 0.12), transparent 30%),
            #f4f7fc;
        color: #172b4d;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .cfox-auth-glow {
        position: absolute;
        width: 420px;
        height: 420px;
        border-radius: 50%;
        filter: blur(70px);
        pointer-events: none;
    }

    .cfox-auth-glow-one {
        top: -180px;
        left: -150px;
        background: rgba(47, 102, 255, 0.12);
    }

    .cfox-auth-glow-two {
        right: -160px;
        bottom: -200px;
        background: rgba(99, 102, 241, 0.10);
    }

    .cfox-auth-shell {
        width: min(1040px, 100%);
        min-height: 650px;
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: 1.08fr 0.92fr;
        overflow: hidden;
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #e3e9f2;
        border-radius: 24px;
        box-shadow:
            0 32px 80px rgba(23, 43, 77, 0.12),
            0 8px 24px rgba(23, 43, 77, 0.05);
        backdrop-filter: blur(18px);
    }

    .cfox-auth-brand-panel {
        padding: 54px 56px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background:
            linear-gradient(145deg, rgba(248, 250, 255, 0.98), rgba(240, 245, 255, 0.94));
        border-right: 1px solid #e3e9f2;
    }

    .cfox-auth-brand-row {
        display: flex;
        align-items: center;
        gap: 13px;
    }

    .cfox-auth-mark,
    .auth-logo {
        width: 44px;
        height: 44px;
        display: grid;
        place-items: center;
        border-radius: 13px;
        color: #fff;
        font-size: 20px;
        font-weight: 800;
        background: linear-gradient(135deg, #2f66ff, #5b7cff);
        box-shadow: 0 10px 24px rgba(47, 102, 255, 0.25);
    }

    .cfox-auth-brand-name,
    .auth-brand h1 {
        margin: 0;
        font-size: 20px;
        line-height: 1;
        font-weight: 800;
        color: #0d1b32;
    }

    .cfox-auth-brand-label,
    .auth-brand p {
        margin: 5px 0 0;
        font-size: 10px;
        letter-spacing: 0.16em;
        font-weight: 700;
        color: #8b98aa;
    }

    .cfox-auth-pitch {
        max-width: 500px;
        margin-top: 40px;
    }

    .cfox-auth-eyebrow {
        margin-bottom: 18px;
        color: #2f66ff;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.16em;
    }

    .cfox-auth-pitch h1 {
        margin: 0;
        color: #0d1b32;
        font-size: clamp(34px, 4vw, 50px);
        line-height: 1.05;
        letter-spacing: -0.045em;
    }

    .cfox-auth-pitch h1 span {
        color: #2f66ff;
    }

    .cfox-auth-pitch p {
        max-width: 470px;
        margin: 22px 0 0;
        color: #68778d;
        font-size: 15px;
        line-height: 1.7;
    }

    .cfox-auth-features {
        display: grid;
        gap: 13px;
        margin-top: 44px;
    }

    .cfox-auth-features div {
        display: flex;
        align-items: center;
        gap: 14px;
        color: #52627a;
        font-size: 13px;
    }

    .cfox-auth-features strong {
        min-width: 24px;
        color: #2f66ff;
        font-size: 10px;
        letter-spacing: 0.08em;
    }

    .cfox-auth-form-panel {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 48px;
        background: #fff;
    }

    .auth-page {
        width: 100%;
        min-height: 0;
        display: block;
        padding: 0;
        background: transparent;
    }

    .auth-card {
        width: 100%;
        max-width: 390px;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
    }

    .auth-brand {
        display: none;
    }

    .auth-heading {
        margin-bottom: 28px;
    }

    .auth-heading h2 {
        margin: 0 0 8px;
        color: #0d1b32;
        font-size: 30px;
        line-height: 1.15;
        letter-spacing: -0.035em;
    }

    .auth-heading p {
        margin: 0;
        color: #68778d;
        font-size: 13px;
        line-height: 1.6;
    }

    .auth-error {
        margin-bottom: 18px;
        padding: 12px 14px;
        border: 1px solid #fecdd3;
        border-radius: 10px;
        background: #fff1f2;
        color: #be123c;
        font-size: 12px;
        line-height: 1.5;
    }

    .auth-card form {
        display: flex;
        flex-direction: column;
    }

    .auth-card form label {
        margin: 0 0 7px;
        color: #34445d;
        font-size: 12px;
        font-weight: 700;
    }

    .auth-card form input {
        width: 100%;
        height: 48px;
        margin: 0 0 17px;
        padding: 0 14px;
        border: 1px solid #d3dce9;
        border-radius: 10px;
        outline: none;
        background: #fff;
        color: #172b4d;
        font-size: 13px;
        transition: border-color .18s ease, box-shadow .18s ease;
    }

    .auth-card form input::placeholder {
        color: #9aa6b6;
    }

    .auth-card form input:focus {
        border-color: #2f66ff;
        box-shadow: 0 0 0 4px rgba(47, 102, 255, 0.09);
    }

    .auth-card form button[type="submit"] {
        width: 100%;
        height: 48px;
        margin-top: 4px;
        border: 0;
        border-radius: 10px;
        background: #2f66ff;
        color: #fff;
        font-size: 13px;
        font-weight: 750;
        box-shadow: 0 10px 22px rgba(47, 102, 255, 0.18);
        transition: transform .18s ease, background .18s ease, box-shadow .18s ease;
    }

    .auth-card form button[type="submit"]:hover:not(:disabled) {
        background: #2457e6;
        transform: translateY(-1px);
        box-shadow: 0 13px 28px rgba(47, 102, 255, 0.24);
    }

    .auth-card form button[type="submit"]:disabled {
        cursor: not-allowed;
        opacity: .65;
    }

    .auth-switch {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 6px;
        margin-top: 24px;
        color: #7a8799;
        font-size: 12px;
    }

    .auth-switch button {
        padding: 0;
        border: 0;
        background: transparent;
        color: #2f66ff;
        font-size: 12px;
        font-weight: 750;
    }

    .auth-switch button:hover {
        text-decoration: underline;
    }

    .cfox-auth-loading {
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
    }

    .cfox-auth-loading-title {
        color: #0d1b32;
        font-size: 24px;
        font-weight: 800;
    }

    .cfox-auth-loading-subtitle {
        color: #68778d;
        font-size: 13px;
    }

    @media (max-width: 820px) {
        .cfox-auth-page {
            padding: 18px;
        }

        .cfox-auth-shell {
            grid-template-columns: 1fr;
            min-height: auto;
        }

        .cfox-auth-brand-panel {
            padding: 32px;
            border-right: 0;
            border-bottom: 1px solid #e3e9f2;
        }

        .cfox-auth-pitch {
            margin-top: 34px;
        }

        .cfox-auth-pitch h1 {
            font-size: 34px;
        }

        .cfox-auth-features {
            display: none;
        }

        .cfox-auth-form-panel {
            padding: 34px 28px;
        }
    }
`;


async function requestJson(path, options = {}, authFetch) {
    const response = await authFetch(`${API}${path}`, options);
    return response;
}

function getDashboard(paymentMethod, options = {}, authFetch) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return requestJson(
        `/transactions/dashboard${query}`,
        options,
        authFetch
    );
}

function getPaymentMethods(options = {}, authFetch) {
    return requestJson(
        "/transactions/analytics/payment-methods",
        options,
        authFetch
    );
}

function getRevenueHistory(
    paymentMethod,
    days = 30,
    options = {},
    authFetch
) {
    const query =
        paymentMethod === "all"
            ? `?days=${days}`
            : `?days=${days}&payment_method=${encodeURIComponent(
                paymentMethod
            )}`;

    return requestJson(
        `/transactions/analytics/revenue-history${query}`,
        options,
        authFetch
    );
}

function getAnomaly(paymentMethod, options = {}, authFetch) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return requestJson(
        `/transactions/analytics/anomaly${query}`,
        options,
        authFetch
    );
}

function getAlerts(paymentMethod, options = {}, authFetch) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return requestJson(
        `/transactions/alerts${query}`,
        options,
        authFetch
    );
}

function getAIInsight(paymentMethod, options = {}, authFetch) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return requestJson(
        `/transactions/analytics/ai-insight${query}`,
        options,
        authFetch
    );
}

function getFinancialActions(paymentMethod, options = {}, authFetch) {
    const query =
        paymentMethod === "all"
            ? ""
            : `?payment_method=${encodeURIComponent(paymentMethod)}`;

    return requestJson(
        `/transactions/analytics/financial-actions${query}`,
        options,
        authFetch
    );
}

function streamCFOChat(question, options = {}, authFetch) {
    return authFetch(`${API}/transactions/cfo/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({question}),
        signal: options.signal,
    });
}


function App() {
    const {
        token,
        user,
        loading: authLoading,
        logout,
        authFetch,
    } = useAuth();

    const [authPage, setAuthPage] =
        useState("login");
    const [theme, setTheme] = useState(() => {
        const saved = localStorage.getItem("cfox-theme");
        return ["system", "light", "dark"].includes(saved)
            ? saved
            : "system";
    });

    useEffect(() => {
        localStorage.setItem("cfox-theme", theme);
    }, [theme]);

    const [dashboard, setDashboard] = useState(null);
    const [paymentMethod, setPaymentMethod] = useState("upi");

    const [paymentMethods, setPaymentMethods] = useState(null);
    const [paymentMethodsLoading, setPaymentMethodsLoading] =
        useState(true);
    const [selectedPaymentMethod, setSelectedPaymentMethod] =
        useState(null);

    const [revenueHistory, setRevenueHistory] = useState(null);
    const [revenueHistoryLoading, setRevenueHistoryLoading] =
        useState(true);

    const aiInsightCache = useRef({});
    const requestControllers = useRef({});
    const requestGeneration = useRef(0);
    const chatBoxRef = useRef(null);

    const [anomaly, setAnomaly] = useState(null);
    const [anomalyLoading, setAnomalyLoading] = useState(true);

    const [alerts, setAlerts] = useState(null);
    const [alertsLoading, setAlertsLoading] = useState(true);
    const [financialActions, setFinancialActions] =
        useState(null);
    const [financialActionsLoading, setFinancialActionsLoading] =
        useState(true);
    const [showSupportingSignals, setShowSupportingSignals] =
        useState(false);

    const [aiInsight, setAiInsight] = useState(null);
    const [aiLoading, setAiLoading] = useState(false);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [question, setQuestion] = useState("");
    const [chatLoading, setChatLoading] = useState(false);
    const [messages, setMessages] = useState([]);

    const [conversations, setConversations] = useState([]);
    const [activeConversationId, setActiveConversationId] =
        useState(null);
    const [conversationsLoading, setConversationsLoading] =
        useState(false);
    const [conversationError, setConversationError] =
        useState("");

    /*
     * =====================================================
     * DASHBOARD
     * =====================================================
     */


    async function loadDashboard() {
        const generation = requestGeneration.current;
        const controller = beginRequest(requestControllers, "loadDashboard");

        try {
            setLoading(true);
            setError("");

            const response = await getDashboard(paymentMethod, {signal: controller.signal}, authFetch);

            const data = await parseApiResponse(
                response,
                "Dashboard request failed"
            );

            if (isCurrentRequest(requestControllers, requestGeneration, "loadDashboard", controller, generation)) {
                setDashboard(data);
            }
        } catch (err) {
            if (err?.name !== "AbortError") {
                console.error("Dashboard error:", err);
                setError("Unable to load financial data.");
            }

        } finally {
            setLoading(false);
        }
    }

    /*
     * =====================================================
     * PAYMENT METHODS
     * =====================================================
     */

    async function loadPaymentMethods() {
        const generation = requestGeneration.current;
        const controller = beginRequest(requestControllers, "loadPaymentMethods");

        try {
            setPaymentMethodsLoading(true);

            const response = await getPaymentMethods({signal: controller.signal}, authFetch);

            const data = await parseApiResponse(
                response,
                "Payment analytics failed"
            );

            if (isCurrentRequest(requestControllers, requestGeneration, "loadPaymentMethods", controller, generation)) {
                setPaymentMethods(data);
            }
        } catch (err) {
            if (err?.name !== "AbortError") {
                console.error(
                    "Payment method analytics error:",
                    err
                );
            }

        } finally {
            setPaymentMethodsLoading(false);
        }
    }

    /*
     * =====================================================
     * REVENUE HISTORY
     * =====================================================
     */

    async function loadRevenueHistory() {
        const generation = requestGeneration.current;
        const controller = beginRequest(requestControllers, "loadRevenueHistory");

        try {
            setRevenueHistoryLoading(true);

            const response = await getRevenueHistory(paymentMethod, 30, {signal: controller.signal}, authFetch);

            const data = await parseApiResponse(
                response,
                "Revenue history failed"
            );

            if (isCurrentRequest(requestControllers, requestGeneration, "loadRevenueHistory", controller, generation)) {
                setRevenueHistory(data);
            }
        } catch (err) {
            if (err?.name !== "AbortError") {
                console.error(
                    "Revenue history error:",
                    err
                );
                setRevenueHistory(null);
            }

        } finally {
            setRevenueHistoryLoading(false);
        }
    }

    /*
     * =====================================================
     * ANOMALY
     * =====================================================
     */

    async function loadAnomaly() {
        const generation = requestGeneration.current;
        const controller = beginRequest(requestControllers, "loadAnomaly");

        try {
            setAnomalyLoading(true);

            const response = await getAnomaly(paymentMethod, {signal: controller.signal}, authFetch);

            const data = await parseApiResponse(
                response,
                "Anomaly request failed"
            );

            if (isCurrentRequest(requestControllers, requestGeneration, "loadAnomaly", controller, generation)) {
                setAnomaly(data);
            }
        } catch (err) {
            if (err?.name !== "AbortError") {
                console.error("Anomaly error:", err);
                setAnomaly(null);
            }

        } finally {
            setAnomalyLoading(false);
        }
    }

    /*
     * =====================================================
     * ALERTS
     * =====================================================
     */

    async function loadAlerts() {
        const generation = requestGeneration.current;
        const controller = beginRequest(requestControllers, "loadAlerts");

        try {
            setAlertsLoading(true);

            const response = await getAlerts(paymentMethod, {signal: controller.signal}, authFetch);

            const data = await parseApiResponse(
                response,
                "Alerts request failed"
            );

            if (isCurrentRequest(requestControllers, requestGeneration, "loadAlerts", controller, generation)) {
                setAlerts(data);
            }
        } catch (err) {
            if (err?.name !== "AbortError") {
                console.error("Alerts error:", err);
                setAlerts(null);
            }

        } finally {
            setAlertsLoading(false);
        }
    }

    /*
     * =====================================================
     * FINANCIAL ACTIONS
     * =====================================================
     */

    async function loadFinancialActions() {
        const generation = requestGeneration.current;
        const controller = beginRequest(
            requestControllers,
            "loadFinancialActions"
        );

        try {
            setFinancialActionsLoading(true);

            const response = await getFinancialActions(
                paymentMethod,
                {signal: controller.signal},
                authFetch
            );

            const data = await parseApiResponse(
                response,
                "Financial actions request failed"
            );

            if (
                isCurrentRequest(
                    requestControllers,
                    requestGeneration,
                    "loadFinancialActions",
                    controller,
                    generation
                )
            ) {
                setFinancialActions(data);
            }
        } catch (err) {
            if (err?.name !== "AbortError") {
                console.error(
                    "Financial actions error:",
                    err
                );
                setFinancialActions(null);
            }
        } finally {
            if (
                isSameRequest(
                    requestControllers,
                    "loadFinancialActions",
                    controller
                )
            ) {
                setFinancialActionsLoading(false);
            }
        }
    }

    /*
     * =====================================================
     * INITIAL LOAD
     * =====================================================
     */

    useEffect(() => {
        if (authLoading || !token || !user) {
            return;
        }

        requestGeneration.current += 1;

        setSelectedPaymentMethod(null);
        setAiInsight(null);

        loadDashboard();
        loadPaymentMethods();
        loadRevenueHistory();
        loadAnomaly();
        loadAlerts();
        loadFinancialActions();
        loadConversations(true);
    }, [paymentMethod, authLoading, token, user]);

    async function refreshFinancialData() {
        aiInsightCache.current = {};
        setAiInsight(null);
        requestGeneration.current += 1;

        await Promise.all([
            loadDashboard(),
            loadPaymentMethods(),
            loadRevenueHistory(),
            loadAnomaly(),
            loadAlerts(),
            loadFinancialActions(),
        ]);
    }

    /*
     * =====================================================
     * AI INSIGHT
     * =====================================================
     */

    async function loadAIInsight(force = false) {
        const cacheKey = paymentMethod;

        if (
            !force &&
            Object.prototype.hasOwnProperty.call(
                aiInsightCache.current,
                cacheKey
            )
        ) {
            setAiInsight(
                aiInsightCache.current[cacheKey]
            );
            return;
        }

        const controller = beginRequest(
            requestControllers,
            "aiInsight"
        );

        try {
            setAiLoading(true);

            const response = await getAIInsight(paymentMethod, {signal: controller.signal}, authFetch);

            const data = await parseApiResponse(
                response,
                "AI insight failed"
            );

            const insight =
                typeof data === "string"
                    ? data
                    : data?.insight ??
                    data?.answer ??
                    data;

            aiInsightCache.current[cacheKey] =
                insight;
            setAiInsight(insight);
        } catch (err) {
            if (err?.name !== "AbortError") {
                console.error(
                    "AI insight error:",
                    err
                );

                setAiInsight({
                    summary:
                        "AI insight is currently unavailable.",
                    severity: "unknown",
                    evidence: [],
                    impact:
                        err?.message ||
                        "Unable to generate an AI insight.",
                    recommendations: [],
                });
            }
        } finally {
            if (
                isSameRequest(
                    requestControllers,
                    "aiInsight",
                    controller
                )
            ) {
                setAiLoading(false);
            }
        }
    }

    /*
     * =====================================================
     * PERSISTENT CFO CONVERSATIONS
     * =====================================================
     */

    function mapConversationMessages(items) {
        if (!Array.isArray(items)) {
            return [];
        }

        return items.map((message) => ({
            id: message.id,
            role: message.role,
            content: message.content || "",
            tool: null,
            created_at: message.created_at,
        }));
    }

    function makeConversationTitle(text) {
        const clean = text
            .replace(/\\s+/g, " ")
            .trim();

        if (!clean) {
            return "New conversation";
        }

        if (clean.length <= 60) {
            return clean;
        }

        return `${clean.slice(0, 57)}...`;
    }

    async function loadConversations(
        selectFirst = false
    ) {
        if (!token || !user) {
            return [];
        }

        setConversationsLoading(true);
        setConversationError("");

        try {
            const data =
                await listConversations(
                    authFetch
                );

            const items =
                Array.isArray(data)
                    ? data
                    : [];

            setConversations(items);

            if (
                selectFirst &&
                items.length > 0
            ) {
                await selectConversation(
                    items[0].id
                );
            }

            return items;
        } catch (err) {
            console.error(
                "Conversation list error:",
                err
            );

            setConversationError(
                "Unable to load saved conversations."
            );

            return [];
        } finally {
            setConversationsLoading(
                false
            );
        }
    }

    async function startNewConversation() {
        if (
            chatLoading ||
            conversationsLoading
        ) {
            return;
        }

        setConversationError("");

        try {
            const conversation =
                await createConversation(
                    "New conversation",
                    authFetch
                );

            setConversations(
                (previous) => [
                    conversation,
                    ...previous,
                ]
            );

            setActiveConversationId(
                conversation.id
            );

            setMessages([]);
            setQuestion("");
        } catch (err) {
            console.error(
                "Create conversation error:",
                err
            );

            setConversationError(
                "Unable to create a new conversation."
            );
        }
    }

    async function selectConversation(
        conversationId
    ) {
        if (
            chatLoading ||
            !conversationId
        ) {
            return;
        }

        setConversationsLoading(true);
        setConversationError("");

        try {
            const conversation =
                await getConversation(
                    conversationId,
                    authFetch
                );

            setActiveConversationId(
                conversation.id
            );

            setMessages(
                mapConversationMessages(
                    conversation.messages
                )
            );

            setQuestion("");
        } catch (err) {
            console.error(
                "Conversation load error:",
                err
            );

            setConversationError(
                "Unable to open that conversation."
            );
        } finally {
            setConversationsLoading(
                false
            );
        }
    }

    async function removeConversation(
        conversationId
    ) {
        if (
            chatLoading ||
            !conversationId
        ) {
            return;
        }

        setConversationError("");

        try {
            await deleteConversation(
                conversationId,
                authFetch
            );

            const remaining =
                conversations.filter(
                    (conversation) =>
                        conversation.id !==
                        conversationId
                );

            setConversations(
                remaining
            );

            if (
                activeConversationId ===
                conversationId
            ) {
                setActiveConversationId(
                    null
                );
                setMessages([]);

                if (
                    remaining.length > 0
                ) {
                    await selectConversation(
                        remaining[0].id
                    );
                }
            }
        } catch (err) {
            console.error(
                "Conversation delete error:",
                err
            );

            setConversationError(
                "Unable to delete that conversation."
            );
        }
    }

    /*
     * =====================================================
     * CHAT
     * =====================================================
     */

    async function sendChatQuestion(chatQuestion) {
        if (chatLoading || !chatQuestion.trim()) {
            return;
        }

        const cleanQuestion = chatQuestion.trim();
        setChatLoading(true);
        setConversationError("");

        let conversationId = activeConversationId;

        const userMessageId = `user-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const assistantMessageId = `assistant-${Date.now()}-${Math.random().toString(36).slice(2)}`;

        try {
            if (!conversationId) {
                const created = await createConversation(
                    makeConversationTitle(cleanQuestion),
                    authFetch
                );

                conversationId = created.id;
                setActiveConversationId(conversationId);
                setConversations((previous) => [created, ...previous]);
            }

            setMessages((previous) => [
                ...previous,
                {
                    id: userMessageId,
                    role: "user",
                    content: cleanQuestion,
                    tool: null,
                    created_at: new Date().toISOString(),
                },
                {
                    id: assistantMessageId,
                    role: "assistant",
                    content: "",
                    tool: null,
                    streaming: true,
                    created_at: new Date().toISOString(),
                },
            ]);

            scrollToChatBox();

            let streamedAnswer = "";
            let streamedTool = null;

            await streamConversationMessage(
                conversationId,
                cleanQuestion,
                authFetch,
                {
                    onMetadata: (metadata) => {
                        streamedTool = metadata?.tool_used || null;

                        setMessages((previous) =>
                            previous.map((message) =>
                                message.id === assistantMessageId
                                    ? {
                                        ...message,
                                        tool: streamedTool,
                                    }
                                    : message
                            )
                        );
                    },

                    onToken: (token) => {
                        streamedAnswer += token;

                        setMessages((previous) =>
                            previous.map((message) =>
                                message.id === assistantMessageId
                                    ? {
                                        ...message,
                                        content: streamedAnswer,
                                        streaming: true,
                                    }
                                    : message
                            )
                        );

                        requestAnimationFrame(() => scrollToChatBox());
                    },

                    onDone: () => {
                        setMessages((previous) =>
                            previous.map((message) =>
                                message.id === assistantMessageId
                                    ? {
                                        ...message,
                                        content: streamedAnswer.trim(),
                                        tool: streamedTool,
                                        streaming: false,
                                    }
                                    : message
                            )
                        );
                    },

                    onError: (error) => {
                        throw error;
                    },
                }
            );

            if (!streamedAnswer.trim()) {
                throw new Error("CFOx returned an empty response.");
            }

            const savedConversation = await getConversation(
                conversationId,
                authFetch
            );

            setActiveConversationId(savedConversation.id);
            setMessages(mapConversationMessages(savedConversation.messages));

            await loadConversations();
        } catch (err) {
            console.error("Persistent streaming chat error:", err);

            setMessages((previous) =>
                previous.map((message) =>
                    message.id === assistantMessageId
                        ? {
                            ...message,
                            content: "Sorry, I couldn't retrieve the financial analysis right now.",
                            tool: null,
                            streaming: false,
                        }
                        : message
                )
            );

            setConversationError(
                err?.message || "Unable to complete the CFO analysis."
            );
        } finally {
            setChatLoading(false);
        }
    }

    async function sendMessage() {
        if (
            !question.trim() ||
            chatLoading
        ) {
            return;
        }

        const currentQuestion =
            question.trim();

        setQuestion("");

        await sendChatQuestion(
            currentQuestion
        );
    }

    function askQuickQuestion(
        quickQuestion
    ) {
        if (chatLoading) {
            return;
        }

        setQuestion("");

        sendChatQuestion(
            quickQuestion
        );
    }

    function scrollToChatBox() {
        requestAnimationFrame(() => {
            chatBoxRef.current?.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        });
    }

    function investigateAction(alert) {
        if (chatLoading || !alert) {
            return;
        }

        const evidence = Array.isArray(
            alert.evidence
        )
            ? alert.evidence
            : [];

        const verifiedEvidence = buildVerifiedEvidence(evidence);

        const question = `
Investigate this CFOx action.

Alert:
${alert.title}

Severity:
${alert.severity}

Message:
${alert.message}

Recommended action:
${alert.recommended_action}

Payment method:
${getPaymentMethodLabel(paymentMethod)}

Verified evidence:
${JSON.stringify(
            verifiedEvidence,
            null,
            2
        )}

Explain why this action is important based ONLY on the verified facts above, what should be checked first, and what practical next steps should be taken.

Rules:
- Use ONLY the verified facts above.
- Do not invent causes, numbers, or events.
- Clearly distinguish observed facts from things that need investigation.
`.trim();

        sendChatQuestion(question);
        scrollToChatBox();
    }

    /*
     * =====================================================
     * FINANCIAL IMPACT INVESTIGATION
     * =====================================================
     */

    function investigateFinancialImpact() {
        if (chatLoading) {
            return;
        }

        const primaryAlerts = Array.isArray(
            alerts?.primary_alerts
        )
            ? alerts.primary_alerts
            : [];

        const evidenceByLabel = {};

        primaryAlerts.forEach((alert) => {
            Object.assign(
                evidenceByLabel,
                buildVerifiedEvidence(alert?.evidence)
            );
        });

        const revenueChange =
            evidenceByLabel[
                "Revenue change"
                ] ?? null;

        const previousRevenue =
            evidenceByLabel[
                "Previous revenue"
                ] ?? null;

        const currentRevenue =
            evidenceByLabel[
                "Current revenue"
                ] ?? null;

        const currentFailureRate =
            evidenceByLabel[
                "Current failure rate"
                ] ?? null;

        const failureRateChange =
            evidenceByLabel[
                "Failure rate change"
                ] ?? null;

        const riskScore =
            evidenceByLabel[
                "Risk score"
                ] ?? null;

        const verifiedData = {
            payment_method:
                paymentMethod === "all"
                    ? "all"
                    : paymentMethod,
            revenue_change_percent:
            revenueChange,
            previous_revenue:
            previousRevenue,
            current_revenue:
            currentRevenue,
            current_failure_rate:
            currentFailureRate,
            failure_rate_change_percentage_points:
            failureRateChange,
            cashflow_risk_score:
            riskScore,
        };

        const question = `
Investigate the financial impact using the verified alert evidence below.

VERIFIED DATA:
${JSON.stringify(
            verifiedData,
            null,
            2
        )}

Explain what these metrics indicate together and recommend practical actions.

Rules:
- Use ONLY the verified data above.
- Do not invent causes, numbers, or correlations.
- Clearly distinguish observed metrics from possible explanations.
- Focus on the financial impact and operational priorities.
`.trim();

        sendChatQuestion(question);
        scrollToChatBox();
    }

    /*
     * =====================================================
     * PAYMENT METHOD INVESTIGATION
     * =====================================================
     */

    function investigatePaymentMethod(method) {
        if (!method || chatLoading) {
            return;
        }

        const current = method.current_period || {};
        const previous = method.previous_period || {};

        const currentRevenue = Number(current.revenue || 0);
        const previousRevenue = Number(previous.revenue || 0);
        const revenueChange = currentRevenue - previousRevenue;

        const questionText = `
Investigate the performance of this payment method.

Payment method: ${method.payment_method}

Verified current-period metrics:
- Total transactions: ${current.total_transactions ?? 0}
- Failed transactions: ${current.failed_transactions ?? 0}
- Failure rate: ${current.failure_rate ?? 0}%

Verified previous-period metrics:
- Total transactions: ${previous.total_transactions ?? 0}
- Failed transactions: ${previous.failed_transactions ?? 0}
- Failure rate: ${previous.failure_rate ?? 0}%

Verified changes:
- Failure rate change: ${method.failure_rate_change ?? 0} percentage points
- Failure rate multiplier: ${method.failure_rate_multiplier ?? "N/A"}x
- Revenue change: ₹${revenueChange.toLocaleString("en-IN", {
            maximumFractionDigits: 2,
        })}

Explain the business significance of this payment method's performance and give practical next steps.

Use ONLY the verified information above.
Do not invent causes, numbers, or facts.
`.trim();

        sendChatQuestion(questionText);
    }

    /*
     * =====================================================
     * ANOMALY INVESTIGATION
     * =====================================================
     */

    function investigateAnomaly() {
        if (
            !anomaly?.anomaly ||
            chatLoading
        ) {
            return;
        }

        const data =
            anomaly.anomaly;

        const paymentMethod =
            anomaly.payment_method ||
            "upi";

        const questionText = `
Investigate this detected financial anomaly.

Payment method: ${paymentMethod}

Verified anomaly score: ${data.score}
Severity: ${data.severity}

Previous failure rate: ${data.previous_failure_rate}%
Current failure rate: ${data.current_failure_rate}%

Failure rate change: ${data.failure_rate_change} percentage points

Failure rate multiplier: ${
            data.failure_rate_multiplier ??
            "N/A"
        }x

Revenue change: ₹${Number(
            data.revenue_change || 0
        ).toLocaleString("en-IN")}

Verified reasons:
${(data.reasons || [])
            .map(
                (reason) =>
                    `- ${reason}`
            )
            .join("\n")}

Explain what this means for the business and give practical actions. Use ONLY these verified facts. Do not invent causes that are not present in the data.
`.trim();

        sendChatQuestion(
            questionText
        );
    }

    function investigateAlert(alert) {
        if (
            chatLoading ||
            !alert
        ) {
            return;
        }

        const evidenceText = Array.isArray(
            alert.evidence
        )
            ? alert.evidence
                .map(
                    (item) =>
                        `- ${item.label}: ${item.value}`
                )
                .join("\n")
            : "";

        const questionText = `
Investigate this CFOx financial alert.

Alert:
${alert.title}

Severity:
${alert.severity}

Message:
${alert.message}

Recommended action:
${alert.recommended_action}

Verified evidence:
${evidenceText}

Explain the business impact and provide practical next steps.

Use ONLY the verified information provided above.
Do not invent causes, numbers, or facts.
`.trim();

        sendChatQuestion(questionText);
    }

    function handleKeyDown(event) {
        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {
            event.preventDefault();
            sendMessage();
        }
    }

    if (loading && token && user) {
        return <LoadingScreen/>;
    }

    /*
     * =====================================================
     * ERROR
     * =====================================================
     */

    if (error) {
        return (
            <ErrorScreen
                error={error}
                onRetry={() => {
                    loadDashboard();
                    loadPaymentMethods();
                    loadRevenueHistory();
                    loadAnomaly();
                    loadAlerts();
                    loadFinancialActions();
                }}
            />
        );
    }

    /*
     * =====================================================
     * DATA
     * =====================================================
     */

    const analysis =
        dashboard?.analysis || {};

    const currentPeriod =
        analysis?.current_period || {};

    const changes =
        analysis?.changes || {};

    const forecast =
        dashboard?.forecast || {};

    const cashflow =
        dashboard?.cashflow || {};

    const anomalyData =
        anomaly?.anomaly || null;

    const forecastDays =
        Array.isArray(
            forecast.forecast
        )
            ? forecast.forecast
            : [];

    const historyDays =
        Array.isArray(
            revenueHistory?.history
        )
            ? revenueHistory.history
            : [];

    const forecastTotal =
        forecastDays.reduce(
            (
                total,
                day
            ) =>
                total +
                Number(
                    day.predicted_revenue ||
                    0
                ),
            0
        );

    const recentAverage =
        Number(
            forecast.recent_average ||
            0
        );

    const cashflowRisk =
        String(
            cashflow.risk ||
            "unknown"
        ).toLowerCase();

    const cashflowScore =
        Number(
            cashflow.risk_score ||
            0
        );

    /*
     * =====================================================
     * AUTH UI
     * =====================================================
     */

    if (authLoading) {
        return (
            <div className="cfox-auth-page">
                <style>{AUTH_STYLES}</style>
                <div className="cfox-auth-loading">
                    <div className="cfox-auth-mark">C</div>
                    <div className="cfox-auth-loading-title">CFOx</div>
                    <div className="cfox-auth-loading-subtitle">
                        Loading your financial workspace...
                    </div>
                </div>
            </div>
        );
    }

    if (!token || !user) {
        return (
            <div className="cfox-auth-page">
                <style>{AUTH_STYLES}</style>

                <div className="cfox-auth-glow cfox-auth-glow-one"/>
                <div className="cfox-auth-glow cfox-auth-glow-two"/>

                <div className="cfox-auth-shell">
                    <div className="cfox-auth-brand-panel">
                        <div className="cfox-auth-brand-row">
                            <div className="cfox-auth-mark">C</div>
                            <div>
                                <div className="cfox-auth-brand-name">CFOx</div>
                                <div className="cfox-auth-brand-label">
                                    FINANCIAL INTELLIGENCE
                                </div>
                            </div>
                        </div>

                        <div className="cfox-auth-pitch">
                            <div className="cfox-auth-eyebrow">
                                FINANCIAL CONTROL CENTER
                            </div>
                            <h1>
                                Understand your money.
                                <br/>
                                <span>Act with confidence.</span>
                            </h1>
                            <p>
                                Revenue, payment performance, risk,
                                cash-flow intelligence and AI-assisted
                                investigation in one workspace.
                            </p>
                        </div>

                        <div className="cfox-auth-features">
                            <div>
                                <strong>01</strong>
                                <span>Real-time financial signals</span>
                            </div>
                            <div>
                                <strong>02</strong>
                                <span>Payment performance analytics</span>
                            </div>
                            <div>
                                <strong>03</strong>
                                <span>AI-powered CFO investigation</span>
                            </div>
                        </div>
                    </div>

                    <div className="cfox-auth-form-panel">
                        {authPage === "register" ? (
                            <Register
                                onLogin={() => setAuthPage("login")}
                            />
                        ) : (
                            <Login
                                onRegister={() => setAuthPage("register")}
                            />
                        )}
                    </div>
                </div>
            </div>
        );
    }

    /*
     * =====================================================
     * MAIN UI
     * ===================================================== */

    return (
        <div
            className="cfox-app"
            data-theme={theme}
        >
            <Header
                paymentMethod={paymentMethod}
                setPaymentMethod={setPaymentMethod}
                loading={loading}
                chatLoading={chatLoading}
                theme={theme}
                setTheme={setTheme}
                user={user}
                onLogout={logout}
            />

            <main className="cfox-main">
                <section className="cfox-page-intro">
                    <div>
                        <div className="cfox-eyebrow">
                            FINANCIAL CONTROL CENTER
                        </div>
                        <h1>Financial overview</h1>
                        <p>
                            Monitor revenue, payment performance,
                            risk and cash-flow signals in one place.
                        </p>
                    </div>

                    <div className="cfox-period-badge">
                        <span className="cfox-live-dot"/>
                        Live financial data
                    </div>
                </section>

                <section className="cfox-kpi-panel">
                    <div className="cfox-section-heading">
                        <div>
                            <div className="cfox-section-kicker">
                                BUSINESS SNAPSHOT
                            </div>
                            <h2>Today at a glance</h2>
                        </div>
                    </div>

                    <KpiCards
                        currentPeriod={currentPeriod}
                        changes={changes}
                    />
                </section>

                <div className="cfox-grid cfox-grid-risk">
                    <div className="cfox-panel">
                        <Anomaly
                            anomalyData={anomalyData}
                            anomalyLoading={anomalyLoading}
                            chatLoading={chatLoading}
                            onInvestigate={investigateAnomaly}
                        />
                    </div>

                    <div className="cfox-panel">
                        <ActionCenter
                            alerts={alerts}
                            financialActions={financialActions}
                            financialActionsLoading={
                                financialActionsLoading
                            }
                            paymentMethod={paymentMethod}
                            onInvestigate={investigateAction}
                            chatLoading={chatLoading}
                        />
                    </div>
                </div>

                <div className="cfox-panel">
                    <PaymentMethods
                        paymentMethods={paymentMethods}
                        paymentMethodsLoading={
                            paymentMethodsLoading
                        }
                        selectedPaymentMethod={
                            selectedPaymentMethod
                        }
                        onSelectPaymentMethod={
                            setSelectedPaymentMethod
                        }
                        investigatePaymentMethod={
                            investigatePaymentMethod
                        }
                        chatLoading={chatLoading}
                    />
                </div>

                <div className="cfox-grid cfox-grid-financial">
                    <div className="cfox-panel">
                        <FinancialImpact
                            dashboard={dashboard}
                            alerts={alerts}
                            paymentMethod={paymentMethod}
                            onInvestigate={
                                investigateFinancialImpact
                            }
                            chatLoading={chatLoading}
                        />
                    </div>

                    <div className="cfox-panel">
                        <FinancialIntelligence
                            cashflow={cashflow}
                            cashflowRisk={cashflowRisk}
                            cashflowScore={cashflowScore}
                            forecast={forecast}
                            forecastDays={forecastDays}
                            forecastTotal={forecastTotal}
                            recentAverage={recentAverage}
                        />
                    </div>
                </div>

                <div className="cfox-panel cfox-transaction-panel">
                    <TransactionManager
                        authFetch={authFetch}
                        onDataChanged={refreshFinancialData}
                    />
                </div>

                <div className="cfox-panel cfox-chart-panel">
                    <HistoricalTrend
                        revenueHistory={revenueHistory}
                    />
                </div>

                <div className="cfox-panel cfox-chart-panel">
                    <RevenueTrend
                        revenueHistoryLoading={
                            revenueHistoryLoading
                        }
                        historyDays={historyDays}
                        forecastDays={forecastDays}
                        paymentMethod={paymentMethod}
                    />
                </div>

                <div className="cfox-panel cfox-ai-panel">
                    <AIInsightSection
                        aiLoading={aiLoading}
                        aiInsight={aiInsight}
                        loadAIInsight={loadAIInsight}
                    />
                </div>

                <div className="cfox-panel cfox-chat-panel">
                    <CFOChat
                        chatBoxRef={chatBoxRef}
                        messages={messages}
                        QUICK_QUESTIONS={QUICK_QUESTIONS}
                        askQuickQuestion={askQuickQuestion}
                        chatLoading={chatLoading}
                        TOOL_LABELS={TOOL_LABELS}
                        question={question}
                        setQuestion={setQuestion}
                        handleKeyDown={handleKeyDown}
                        sendMessage={sendMessage}
                        conversations={conversations}
                        activeConversationId={
                            activeConversationId
                        }
                        conversationsLoading={
                            conversationsLoading
                        }
                        conversationError={
                            conversationError
                        }
                        onNewConversation={
                            startNewConversation
                        }
                        onSelectConversation={
                            selectConversation
                        }
                        onDeleteConversation={
                            removeConversation
                        }
                    />
                </div>
            </main>
        </div>
    )
}


export default App;