import React, { useState, useCallback, useRef, useEffect } from "react";
import { User, Bot } from "lucide-react";
import {
  sendChatMessage,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

interface Message {
  role: "user" | "assistant";
  content: string;
  data?: Record<string, unknown>;
}

const ChatPage: React.FC = () => {
  const { activeSheet, isLoading } = useWorkbook();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Halo! Saya asisten AI Excel Genius. Tanyakan apa saja tentang data Excel Anda, atau minta bantuan membuat rumus, menganalisis tren, dan lainnya.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Build workbook context from activeSheet
  const workbookContext = React.useMemo(() => {
    if (activeSheet) {
      return [{
        name: activeSheet.sheetName,
        headers: activeSheet.headers,
        data: activeSheet.data,
      }];
    }
    return undefined;
  }, [activeSheet]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setError("");

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      if (!workbookContext) {
        throw new Error("Belum ada data workbook.");
      }
      const res = await sendChatMessage(text, workbookContext);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.reply,
          data: res.data ?? undefined,
        },
      ]);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Gagal mengirim pesan.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [input, loading, workbookContext]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div className="page chat-page">
      <h2 className="page-title">Chat</h2>

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

      {isLoading && <LoadingSpinner message="Memuat data workbook..." />}

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble chat-${msg.role}`}>
            <div className="chat-bubble-avatar">
              {msg.role === "user" ? <User size={18} /> : <Bot size={18} />}
            </div>
            <div className="chat-bubble-content">
              <div className="chat-bubble-text">{msg.content}</div>
              {msg.data && (
                <div className="chat-bubble-data">
                  <pre>{JSON.stringify(msg.data, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-bubble chat-assistant">
            <div className="chat-bubble-avatar">🤖</div>
            <div className="chat-bubble-content">
              <div className="chat-typing">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          ref={inputRef}
          className="chat-input"
          rows={2}
          placeholder="Tanyakan tentang data Anda..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="btn btn-primary chat-send-btn"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          {loading ? "..." : "Kirim"}
        </button>
      </div>
    </div>
  );
};

export default ChatPage;
