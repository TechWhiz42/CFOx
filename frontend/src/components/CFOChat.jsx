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
}) {
    return (


            <section
                style={{
                    background:
                        "rgba(255,255,255,0.04)",
                    border:
                        "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "16px",
                    padding: "24px",
                }}

                ref={chatBoxRef}>
                <div
                    style={{
                        marginBottom:
                            "16px",
                    }}
                >
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
                            fontSize: "13px",
                        }}
                    >
                        Ask questions about your
                        financial data
                    </p>
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
                                (
                                    item
                                ) => (
                                    <button
                                        key={
                                            item.question
                                        }
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
                            <br />
                            <br />
                            "Which payment method
                            is performing worst?"
                            <br />
                            <br />
                            "Why did revenue fall?"
                            <br />
                            <br />
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
                                    index
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
            </section>
    );
}

export default CFOChat;