function formatConversationDate(value) {
    if (!value) {
        return "";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "";
    }

    return date.toLocaleDateString(
        "en-IN",
        {
            day: "2-digit",
            month: "short",
        }
    );
}

function conversationTitle(conversation) {
    return (
        conversation?.title?.trim() ||
        "New conversation"
    );
}

function CFOChat({
                     chatBoxRef,
                     messages,
                     QUICK_QUESTIONS,
                     askQuickQuestion,
                     chatLoading,
                     TOOL_LABELS,
                     question,
                     setQuestion,
                     handleKeyDown,
                     sendMessage,

                     conversations = [],
                     activeConversationId = null,
                     conversationsLoading = false,
                     conversationError = "",
                     onNewConversation,
                     onSelectConversation,
                     onDeleteConversation,
                 }) {
    return (
        <section
            ref={chatBoxRef}
            style={{
                background:
                    "rgba(255,255,255,0.04)",
                border:
                    "1px solid rgba(255,255,255,0.08)",
                borderRadius: "16px",
                padding: "24px",
            }}
        >
            <div
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "240px minmax(0, 1fr)",
                    gap: "22px",
                }}
            >
                {/* =================================================
                    CONVERSATION SIDEBAR
                ================================================== */}

                <aside
                    style={{
                        borderRight:
                            "1px solid rgba(255,255,255,0.08)",
                        paddingRight: "18px",
                        minWidth: 0,
                    }}
                >
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent:
                                "space-between",
                            gap: "8px",
                            marginBottom: "14px",
                        }}
                    >
                        <div>
                            <div
                                style={{
                                    fontSize: "12px",
                                    fontWeight: 700,
                                    letterSpacing:
                                        "0.04em",
                                    opacity: 0.75,
                                }}
                            >
                                CONVERSATIONS
                            </div>

                            <div
                                style={{
                                    fontSize: "11px",
                                    opacity: 0.4,
                                    marginTop: "4px",
                                }}
                            >
                                Your CFOx history
                            </div>
                        </div>

                        <button
                            type="button"
                            onClick={
                                onNewConversation
                            }
                            disabled={chatLoading}
                            style={{
                                width: "32px",
                                height: "32px",
                                padding: 0,
                                borderRadius:
                                    "9px",
                                border:
                                    "1px solid rgba(255,255,255,0.12)",
                                background:
                                    "rgba(255,255,255,0.06)",
                                color: "inherit",
                                cursor:
                                    chatLoading
                                        ? "not-allowed"
                                        : "pointer",
                                opacity:
                                    chatLoading
                                        ? 0.45
                                        : 1,
                                fontSize: "18px",
                                lineHeight: 1,
                            }}
                            aria-label="New conversation"
                            title="New conversation"
                        >
                            +
                        </button>
                    </div>

                    {conversationError && (
                        <div
                            style={{
                                padding: "9px 10px",
                                marginBottom: "10px",
                                borderRadius: "9px",
                                background:
                                    "rgba(239,68,68,0.10)",
                                border:
                                    "1px solid rgba(239,68,68,0.18)",
                                color: "#fca5a5",
                                fontSize: "11px",
                                lineHeight: 1.4,
                            }}
                        >
                            {conversationError}
                        </div>
                    )}

                    <div
                        style={{
                            display: "flex",
                            flexDirection:
                                "column",
                            gap: "6px",
                            maxHeight: "430px",
                            overflowY: "auto",
                        }}
                    >
                        {conversationsLoading && (
                            <div
                                style={{
                                    padding:
                                        "12px 10px",
                                    fontSize: "11px",
                                    opacity: 0.45,
                                }}
                            >
                                Loading conversations...
                            </div>
                        )}

                        {!conversationsLoading &&
                            conversations.length ===
                            0 && (
                                <div
                                    style={{
                                        padding:
                                            "14px 10px",
                                        fontSize: "11px",
                                        lineHeight:
                                            1.6,
                                        opacity: 0.45,
                                    }}
                                >
                                    No saved conversations yet.
                                    <br/>
                                    Start asking CFOx to
                                    create one.
                                </div>
                            )}

                        {conversations.map(
                            (conversation) => {
                                const active =
                                    conversation.id ===
                                    activeConversationId;

                                return (
                                    <div
                                        key={
                                            conversation.id
                                        }
                                        style={{
                                            display:
                                                "flex",
                                            alignItems:
                                                "center",
                                            gap: "5px",
                                            borderRadius:
                                                "10px",
                                            background:
                                                active
                                                    ? "rgba(99,102,241,0.14)"
                                                    : "transparent",
                                            border:
                                                active
                                                    ? "1px solid rgba(99,102,241,0.22)"
                                                    : "1px solid transparent",
                                        }}
                                    >
                                        <button
                                            type="button"
                                            onClick={() =>
                                                onSelectConversation(
                                                    conversation.id
                                                )
                                            }
                                            disabled={
                                                chatLoading
                                            }
                                            style={{
                                                flex: 1,
                                                minWidth:
                                                    0,
                                                padding:
                                                    "10px",
                                                border: 0,
                                                background:
                                                    "transparent",
                                                color:
                                                    "inherit",
                                                textAlign:
                                                    "left",
                                                cursor:
                                                    chatLoading
                                                        ? "not-allowed"
                                                        : "pointer",
                                                opacity:
                                                    chatLoading
                                                        ? 0.55
                                                        : 1,
                                            }}
                                        >
                                            <div
                                                style={{
                                                    overflow:
                                                        "hidden",
                                                    textOverflow:
                                                        "ellipsis",
                                                    whiteSpace:
                                                        "nowrap",
                                                    fontSize:
                                                        "11px",
                                                    fontWeight:
                                                        active
                                                            ? 700
                                                            : 600,
                                                }}
                                            >
                                                {conversationTitle(
                                                    conversation
                                                )}
                                            </div>

                                            <div
                                                style={{
                                                    marginTop:
                                                        "4px",
                                                    fontSize:
                                                        "9px",
                                                    opacity:
                                                        0.4,
                                                }}
                                            >
                                                {formatConversationDate(
                                                    conversation.updated_at ||
                                                    conversation.created_at
                                                )}
                                            </div>
                                        </button>

                                        <button
                                            type="button"
                                            onClick={() =>
                                                onDeleteConversation(
                                                    conversation.id
                                                )
                                            }
                                            disabled={
                                                chatLoading
                                            }
                                            aria-label={`Delete ${conversationTitle(
                                                conversation
                                            )}`}
                                            title="Delete conversation"
                                            style={{
                                                width:
                                                    "26px",
                                                height:
                                                    "26px",
                                                marginRight:
                                                    "5px",
                                                padding: 0,
                                                border: 0,
                                                borderRadius:
                                                    "7px",
                                                background:
                                                    "transparent",
                                                color:
                                                    "inherit",
                                                opacity:
                                                    0.35,
                                                cursor:
                                                    chatLoading
                                                        ? "not-allowed"
                                                        : "pointer",
                                            }}
                                        >
                                            ×
                                        </button>
                                    </div>
                                );
                            }
                        )}
                    </div>
                </aside>

                {/* =================================================
                    CHAT
                ================================================== */}

                <div
                    style={{
                        minWidth: 0,
                    }}
                >
                    <div
                        style={{
                            display: "flex",
                            alignItems:
                                "flex-start",
                            justifyContent:
                                "space-between",
                            gap: "14px",
                            marginBottom: "16px",
                        }}
                    >
                        <div>
                            <h2
                                style={{
                                    margin: 0,
                                }}
                            >
                                Ask CFOx
                            </h2>

                            <p
                                style={{
                                    margin:
                                        "6px 0 0",
                                    opacity: 0.5,
                                    fontSize:
                                        "13px",
                                }}
                            >
                                Ask questions about your
                                financial data
                            </p>
                        </div>

                        {activeConversationId && (
                            <div
                                style={{
                                    padding:
                                        "6px 9px",
                                    borderRadius:
                                        "999px",
                                    background:
                                        "rgba(255,255,255,0.05)",
                                    fontSize: "9px",
                                    opacity: 0.45,
                                    whiteSpace:
                                        "nowrap",
                                }}
                            >
                                Saved
                            </div>
                        )}
                    </div>

                    {messages.length === 0 && (
                        <div
                            style={{
                                marginBottom:
                                    "20px",
                            }}
                        >
                            <div
                                style={{
                                    fontSize:
                                        "12px",
                                    opacity: 0.5,
                                    marginBottom:
                                        "10px",
                                }}
                            >
                                Quick analysis
                            </div>

                            <div
                                style={{
                                    display:
                                        "flex",
                                    flexWrap:
                                        "wrap",
                                    gap: "8px",
                                }}
                            >
                                {QUICK_QUESTIONS.map(
                                    (item) => (
                                        <button
                                            key={
                                                item.question
                                            }
                                            type="button"
                                            onClick={() =>
                                                askQuickQuestion(
                                                    item.question
                                                )
                                            }
                                            disabled={
                                                chatLoading
                                            }
                                        >
                                            {
                                                item.label
                                            }
                                        </button>
                                    )
                                )}
                            </div>
                        </div>
                    )}

                    <div
                        style={{
                            minHeight:
                                "180px",
                            maxHeight:
                                "500px",
                            overflowY:
                                "auto",
                            marginBottom:
                                "16px",
                        }}
                    >
                        {messages.length ===
                            0 && (
                                <div
                                    style={{
                                        opacity:
                                            0.5,
                                        lineHeight:
                                            1.7,
                                        padding:
                                            "16px 0",
                                    }}
                                >
                                    Ask CFOx something
                                    like:
                                    <br/>
                                    <br/>
                                    "Which payment method
                                    is performing worst?"
                                    <br/>
                                    <br/>
                                    "Why did revenue fall?"
                                    <br/>
                                    <br/>
                                    "What is my biggest
                                    financial risk?"
                                </div>
                            )}

                        {messages.map(
                            (
                                message,
                                index
                            ) => (
                                <div
                                    key={
                                        message.id ||
                                        `${message.role}-${index}`
                                    }
                                    style={{
                                        marginBottom:
                                            "16px",
                                    }}
                                >
                                    <div
                                        style={{
                                            padding:
                                                "14px",
                                            borderRadius:
                                                "12px",
                                            background:
                                                message.role ===
                                                "user"
                                                    ? "rgba(255,255,255,0.06)"
                                                    : "rgba(99,102,241,0.10)",
                                        }}
                                    >
                                        <div
                                            style={{
                                                display:
                                                    "flex",
                                                justifyContent:
                                                    "space-between",
                                                alignItems:
                                                    "center",
                                                marginBottom:
                                                    "7px",
                                            }}
                                        >
                                            <div
                                                style={{
                                                    fontSize:
                                                        "12px",
                                                    opacity:
                                                        0.5,
                                                }}
                                            >
                                                {message.role ===
                                                "user"
                                                    ? "You"
                                                    : "CFOx"}
                                            </div>

                                            {message.role ===
                                                "assistant" &&
                                                message.tool && (
                                                    <div
                                                        style={{
                                                            fontSize:
                                                                "10px",
                                                            padding:
                                                                "4px 8px",
                                                            borderRadius:
                                                                "999px",
                                                            background:
                                                                "rgba(255,255,255,0.07)",
                                                            opacity:
                                                                0.7,
                                                        }}
                                                    >
                                                        {TOOL_LABELS[
                                                                message.tool
                                                                ] ||
                                                            "CFOx"}
                                                    </div>
                                                )}
                                        </div>

                                        <div
                                            style={{
                                                whiteSpace:
                                                    "pre-wrap",
                                                lineHeight:
                                                    1.6,
                                            }}
                                        >
                                            {message.content ||
                                                (message.role ===
                                                "assistant" &&
                                                chatLoading
                                                    ? "Analyzing..."
                                                    : "")}
                                        </div>
                                    </div>
                                </div>
                            )
                        )}
                    </div>

                    <div
                        style={{
                            display:
                                "flex",
                            gap: "10px",
                        }}
                    >
                        <textarea
                            value={
                                question
                            }
                            onChange={(
                                event
                            ) =>
                                setQuestion(
                                    event.target.value
                                )
                            }
                            onKeyDown={
                                handleKeyDown
                            }
                            placeholder="Ask CFOx about your finances..."
                            rows={2}
                            style={{
                                flex: 1,
                                resize: "none",
                                padding: "12px",
                                borderRadius:
                                    "10px",
                                border:
                                    "1px solid rgba(255,255,255,0.12)",
                                background:
                                    "rgba(0,0,0,0.2)",
                                color:
                                    "#ffffff",
                                outline: "none",
                            }}
                        />

                        <button
                            type="button"
                            onClick={
                                sendMessage
                            }
                            disabled={
                                chatLoading ||
                                !question.trim()
                            }
                        >
                            {chatLoading
                                ? "Analyzing..."
                                : "Ask"}
                        </button>
                    </div>
                </div>
            </div>
        </section>
    );
}

export default CFOChat;