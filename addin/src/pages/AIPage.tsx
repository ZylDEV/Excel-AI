import React, { useState, useCallback, useRef, useEffect } from "react";
import { Send, Bot, User, FileSpreadsheet, Copy, Check } from "lucide-react";
import { generateFormula, sendChatMessage } from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import ErrorAlert from "../components/ErrorAlert";

interface Message {
  role: "user" | "assistant";
  content: string;
  formula?: string;
}

const AIPage: React.FC = () => {
  const { activeSheet, isLoading: wbLoading } = useWorkbook();
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Halo! Saya asisten AI Excel Genius. Tanyakan apa saja tentang Excel — buat rumus, analisis data, atau tanya tentang spreadsheet Anda." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setError("");

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const isFormulaRequest = /(?:buat|buatkan|bikin|rumus|formula|fungsi)\b/i.test(text) && !/\b(?:jelaskan|apa itu|bagaimana|how|what)\b/i.test(text);
      let reply: string;
      let formula: string | undefined;

      if (isFormulaRequest) {
        const ctx = activeSheet ? `Sheet: ${activeSheet.sheetName}\nHeaders: ${activeSheet.headers.join(", ")}\nRows: ${activeSheet.data.length}` : "";
        const res = await generateFormula(text, ctx);
        reply = res.explanation + (res.example ? `\n\nContoh: ${res.example}` : "");
        formula = res.formula;
      } else {
        const context = activeSheet ? [{ name: activeSheet.sheetName, headers: activeSheet.headers, data: activeSheet.data }] : undefined;
        const res = await sendChatMessage(text, context);
        reply = res.reply;
      }

      setMessages((prev) => [...prev, { role: "assistant", content: reply, formula }]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Gagal memproses.");
    } finally {
      setLoading(false);
    }
  }, [input, loading, activeSheet]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  }, [handleSend]);

  const handleCopy = useCallback((text: string, idx: number) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 2000);
    });
  }, []);

  const hl = (f: string) => f
    .replace(/(=?[A-Z]+)(?=\()/g, '<span style="color:#89b4fa;font-weight:700">$1</span>')
    .replace(/([""][^""]*[""])/g, '<span style="color:#a6e3a1">$1</span>')
    .replace(/(\b\d+(?:\.\d+)?\b)/g, '<span style="color:#fab387">$1</span>')
    .replace(/([(),])/g, '<span style="color:#94e2d5">$1</span>');

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      
      <div style={{ position: "sticky", top: 0, zIndex: 10, background: "var(--grey-50)", paddingBottom: 8 }}>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: "var(--grey-900)" }}>AI Assistant</h2>
        {activeSheet && (
          <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 4, padding: "3px 8px", background: "var(--primary-light)", borderRadius: 6, fontSize: 10, color: "var(--primary-dark)" }}>
            <FileSpreadsheet size={11} />
            <span>{activeSheet.sheetName} — {activeSheet.data.length} baris</span>
          </div>
        )}
        {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      </div>

      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, padding: "4px 0" }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", gap: 6, maxWidth: "90%", alignSelf: msg.role === "user" ? "flex-end" : "flex-start", flexDirection: msg.role === "user" ? "row-reverse" : "row" }}>
            
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 26, height: 26, borderRadius: "50%", flexShrink: 0, background: msg.role === "user" ? "var(--primary)" : "var(--grey-200)", color: msg.role === "user" ? "white" : "var(--grey-600)" }}>
              {msg.role === "user" ? <User size={14} /> : <Bot size={14} />}
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 4, maxWidth: "100%" }}>
              {msg.formula && (
                <div style={{ position: "relative", background: "#1e1e2e", borderRadius: 8, padding: "10px 12px", overflowX: "auto" }}>
                  <code style={{ color: "#cdd6f4", fontSize: 13, fontFamily: "'Cascadia Code','Fira Code',Consolas,monospace", lineHeight: 1.6, wordBreak: "break-all" }} dangerouslySetInnerHTML={{ __html: hl(msg.formula) }} />
                  <button onClick={() => handleCopy(msg.formula!, i)} style={{ position: "absolute", top: 4, right: 4, display: "flex", alignItems: "center", gap: 3, padding: "2px 6px", border: "none", borderRadius: 3, fontSize: 10, cursor: "pointer", background: copiedIdx === i ? "rgba(76,175,80,0.2)" : "rgba(255,255,255,0.12)", color: copiedIdx === i ? "#81c784" : "rgba(255,255,255,0.5)" }}>
                    {copiedIdx === i ? <Check size={11} /> : <Copy size={11} />}
                  </button>
                </div>
              )}

              <div style={{ padding: msg.formula ? "6px 0 0" : "8px 12px", borderRadius: msg.formula ? 0 : 10, fontSize: 13, lineHeight: 1.6, wordBreak: "break-word", background: msg.role === "user" ? "var(--primary)" : "var(--grey-100)", color: msg.role === "user" ? "white" : "var(--grey-800)", borderBottomRightRadius: msg.role === "user" && !msg.formula ? 4 : 10, borderBottomLeftRadius: msg.role !== "user" && !msg.formula ? 4 : 10 }}>
                {msg.content.split("\n").map((line, li) => (
                  <p key={li} style={{ margin: 0 }}>{line || "\u00A0"}</p>
                ))}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 26, height: 26, borderRadius: "50%", background: "var(--grey-200)" }}>
              <Bot size={14} style={{ color: "var(--grey-500)" }} />
            </div>
            <div style={{ display: "flex", gap: 3, padding: "8px 12px", background: "var(--grey-100)", borderRadius: 10, borderBottomLeftRadius: 4 }}>
              {[0, 1, 2].map((d) => (
                <div key={d} style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--grey-400)", animation: "typingBounce 1.4s infinite ease-in-out", animationDelay: `${d * 0.2}s` }} />
              ))}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div style={{ position: "sticky", bottom: 0, zIndex: 10, padding: "8px 0 4px" }}>
        <div className="ai-input-glow">
          <div style={{ display: "flex", gap: 8, alignItems: "flex-end", background: "var(--white)", borderRadius: 13, padding: "6px 6px 6px 14px" }}>
            <textarea ref={inputRef} rows={1} value={input}
              onChange={(e) => { setInput(e.target.value); e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px"; }}
              onKeyDown={handleKeyDown}
              placeholder="Tanya apa saja..."
              disabled={loading || wbLoading}
              style={{ flex: 1, border: "none", padding: "6px 0", fontSize: 14, fontFamily: "inherit", resize: "none", outline: "none", color: "var(--grey-800)", lineHeight: 1.5, maxHeight: 120, background: "transparent" }}
            />
            <button onClick={handleSend} disabled={loading || !input.trim()}
              style={{ padding: "8px 10px", border: "none", borderRadius: 10, background: input.trim() ? "var(--primary)" : "var(--grey-200)", color: input.trim() ? "white" : "var(--grey-400)", cursor: loading || !input.trim() ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.15s", flexShrink: 0, width: 34, height: 34 }}>
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>

    </div>
  );
};

export default AIPage;
