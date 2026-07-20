import React, { useState, useEffect } from "react";
import { Settings, Save, Loader2, Search, CheckCircle, XCircle, ExternalLink } from "lucide-react";
import { validateApiKey } from "../services/api";

const PROVIDERS = [
  { id: "openai", label: "OpenAI", keyPlaceholder: "sk-...", docs: "https://platform.openai.com/api-keys", needsKey: true },
  { id: "deepseek", label: "DeepSeek", keyPlaceholder: "sk-...", docs: "https://platform.deepseek.com/api_keys", needsKey: true },
  { id: "mistral", label: "Mistral AI", keyPlaceholder: "Paste Mistral API key", docs: "https://console.mistral.ai/api-keys/", needsKey: true },
  { id: "groq", label: "Groq", keyPlaceholder: "gsk_...", docs: "https://console.groq.com/keys", needsKey: true },
  { id: "together", label: "Together AI", keyPlaceholder: "Paste Together API key", docs: "https://api.together.ai/settings/api-keys", needsKey: true },
  { id: "openrouter", label: "OpenRouter", keyPlaceholder: "sk-or-...", docs: "https://openrouter.ai/keys", needsKey: true },
  { id: "gemini", label: "Google Gemini", keyPlaceholder: "AIza...", docs: "https://aistudio.google.com/apikey", needsKey: true },
  { id: "claude", label: "Anthropic Claude", keyPlaceholder: "sk-ant-...", docs: "https://console.anthropic.com/", needsKey: true },
  { id: "ollama", label: "Ollama (Local)", keyPlaceholder: "Not needed", docs: "https://ollama.ai/", needsKey: false },
];

const SettingsPage: React.FC = () => {
  const [apiKey, setApiKey] = useState(localStorage.getItem("openai_api_key") || "");
  const [provider, setProvider] = useState(localStorage.getItem("llm_provider") || "openai");
  const [ollamaUrl, setOllamaUrl] = useState(localStorage.getItem("ollama_base_url") || "http://localhost:11434");
  const [apiEndpoint, setApiEndpoint] = useState(localStorage.getItem("api_endpoint") || "");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ valid: boolean; message: string } | null>(null);

  const currentProvider = PROVIDERS.find((p) => p.id === provider) || PROVIDERS[0];

  useEffect(() => {
    const saved = localStorage.getItem("openai_api_key") || "";
    const savedProv = localStorage.getItem("llm_provider") || "openai";
    setApiKey(saved);
    setProvider(savedProv);
    setOllamaUrl(localStorage.getItem("ollama_base_url") || "http://localhost:11434");
    setApiEndpoint(localStorage.getItem("api_endpoint") || "");
  }, []);

  const handleSave = () => {
    localStorage.setItem("openai_api_key", apiKey);
    localStorage.setItem("llm_provider", provider);
    localStorage.setItem("ollama_base_url", ollamaUrl);
    localStorage.setItem("api_endpoint", apiEndpoint);
    alert("Pengaturan tersimpan!");
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await validateApiKey(apiKey, provider);
      setTestResult(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Gagal tes koneksi.";
      setTestResult({ valid: false, message: msg });
    } finally {
      setTesting(false);
    }
  };

  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newProvider = e.target.value;
    setProvider(newProvider);
    setTestResult(null);
    // Load saved key for this provider if exists
    const savedKey = localStorage.getItem(`${newProvider}_api_key`);
    if (savedKey) setApiKey(savedKey);
    else setApiKey("");
  };

  return (
    <div className="page">
      <h2 className="page-title">Pengaturan</h2>

      <div className="card">
        <label className="form-label">AI Provider</label>
        <select className="form-select" value={provider} onChange={handleProviderChange}>
          {PROVIDERS.map((p) => (
            <option key={p.id} value={p.id}>{p.label}</option>
          ))}
        </select>
        <p className="text-muted" style={{ marginTop: 4 }}>
          Pilih penyedia AI yang ingin digunakan.&nbsp;
          <a href={currentProvider.docs} target="_blank" rel="noopener noreferrer" style={{ color: "#1565c0", textDecoration: "underline" }}>
            Dapatkan API Key <ExternalLink size={11} />
          </a>
        </p>
      </div>

      <div className="card">
        <label className="form-label">API Key</label>
        <input
          className="form-input input-password"
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder={currentProvider.keyPlaceholder}
          disabled={!currentProvider.needsKey}
        />
      </div>

      {provider === "ollama" && (
        <div className="card">
          <label className="form-label">Ollama Base URL</label>
          <input className="form-input" type="text" value={ollamaUrl}
            onChange={(e) => setOllamaUrl(e.target.value)} placeholder="http://localhost:11434" />
        </div>
      )}

      {provider === "deepseek" && (
        <div className="card">
          <label className="form-label">API Endpoint (opsional)</label>
          <input className="form-input" type="text" value={apiEndpoint}
            onChange={(e) => setApiEndpoint(e.target.value)} placeholder="https://api.deepseek.com/v1" />
        </div>
      )}

      <div className="button-row">
        <button onClick={handleSave} className="btn btn-primary">
          <Save size={16} /> Simpan
        </button>
        <button onClick={handleTest} className="btn btn-secondary"
          disabled={!apiKey || testing || !currentProvider.needsKey}>
          {testing ? <><Loader2 size={16} className="spin" /> Mengecek...</>
            : <><Search size={16} /> Tes Koneksi</>}
        </button>
      </div>

      {testResult && (
        <div className={`alert ${testResult.valid ? "alert-success" : "alert-error"}`}>
          {testResult.valid
            ? <><CheckCircle size={16} /> Koneksi berhasil!</>
            : <><XCircle size={16} /> Gagal: {testResult.message}</>}
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
