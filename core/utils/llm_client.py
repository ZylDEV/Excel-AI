"""Unified LLM client supporting 10+ AI providers."""

import json
import logging
import os

from openai import OpenAI

logger = logging.getLogger(__name__)

# ── Provider registry ──────────────────────────────────────────────────
# Each entry: { label, env_key, default_model, base_url (None = official) }
PROVIDERS = {
    # OpenAI-compatible API format
    "openai": {
        "label": "OpenAI",
        "default_model": "gpt-4o",
        "base_url": None,  # official OpenAI API
        "key_placeholder": "sk-...",
        "docs": "https://platform.openai.com/api-keys",
    },
    "deepseek": {
        "label": "DeepSeek",
        "default_model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "key_placeholder": "sk-...",
        "docs": "https://platform.deepseek.com/api_keys",
    },
    "mistral": {
        "label": "Mistral AI",
        "default_model": "mistral-large-latest",
        "base_url": "https://api.mistral.ai/v1",
        "key_placeholder": "Paste Mistral API key",
        "docs": "https://console.mistral.ai/api-keys/",
    },
    "groq": {
        "label": "Groq",
        "default_model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "key_placeholder": "gsk_...",
        "docs": "https://console.groq.com/keys",
    },
    "together": {
        "label": "Together AI",
        "default_model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "base_url": "https://api.together.xyz/v1",
        "key_placeholder": "Paste Together API key",
        "docs": "https://api.together.ai/settings/api-keys",
    },
    "openrouter": {
        "label": "OpenRouter",
        "default_model": "openai/gpt-4o",
        "base_url": "https://openrouter.ai/api/v1",
        "key_placeholder": "sk-or-...",
        "docs": "https://openrouter.ai/keys",
    },
    # Native SDK providers
    "gemini": {
        "label": "Google Gemini",
        "default_model": "gemini-2.0-flash",
        "base_url": None,
        "key_placeholder": "AIza...",
        "docs": "https://aistudio.google.com/apikey",
    },
    "claude": {
        "label": "Anthropic Claude",
        "default_model": "claude-sonnet-4-20250514",
        "base_url": None,
        "key_placeholder": "sk-ant-...",
        "docs": "https://console.anthropic.com/",
    },
    # Local
    "ollama": {
        "label": "Ollama (Local)",
        "default_model": "llama3.2",
        "base_url": None,
        "key_placeholder": "Not needed",
        "docs": "https://ollama.ai/",
    },
}


class LLMClient:
    """Unified client that routes to any supported AI provider.

    Parameters
    ----------
    api_key : str | None
        API key for the provider. If None, falls back to the env variable
        ``{PROVIDER}_api_key`` (e.g. ``openai_api_key``, ``deepseek_api_key``).
    provider : str | None
        Identifier from ``PROVIDERS``. Auto-detected from key format when
        ``api_key`` is given and ``provider`` is not explicitly set.
    model : str | None
        Model name override.
    """

    def __init__(
        self,
        api_key: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ):
        # ── Detect provider from key format ────────────────────────
        if api_key and not provider:
            if api_key.startswith("sk-ant"):
                provider = "claude"
            elif api_key.startswith("AIza"):
                provider = "gemini"
            elif api_key.startswith("gsk_"):
                provider = "groq"
            elif api_key.startswith("sk-or"):
                provider = "openrouter"
            elif api_key.startswith("sk-"):
                provider = "openai"
            else:
                provider = "openai"  # fallback

        self.provider = (provider or "openai").lower()
        provider_cfg = PROVIDERS.get(self.provider, PROVIDERS["openai"])

        # ── Resolve API key ────────────────────────────────────────
        env_key_name = f"{self.provider}_api_key"
        self.api_key = api_key or os.environ.get(env_key_name, "") or ""

        # ── Resolve model ──────────────────────────────────────────
        self.model = model or provider_cfg["default_model"]

        # ── Resolve base_url (for OpenAI-compatible providers) ─────
        self.base_url = provider_cfg.get("base_url")

        # ── Init client ────────────────────────────────────────────
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.provider in ("openai", "deepseek", "mistral", "groq", "together", "openrouter"):
            # All use OpenAI-compatible API
            kwargs = {"api_key": self.api_key or None}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)

        elif self.provider == "gemini":
            import google.generativeai as genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
            self._client = genai

        elif self.provider == "claude":
            # Lazy import; anthropic SDK may not be installed
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ImportError(
                    "Anthropic SDK not installed. Run: pip install anthropic"
                )
            self._client = Anthropic(api_key=self.api_key or None)

        elif self.provider == "ollama":
            self._client = None  # Uses raw httpx

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    # ── Public API ─────────────────────────────────────────────────────

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        try:
            if self.provider in ("openai", "deepseek", "mistral", "groq", "together", "openrouter"):
                return self._call_openai_compat(prompt, system_prompt)
            elif self.provider == "gemini":
                return self._call_gemini(prompt, system_prompt)
            elif self.provider == "claude":
                return self._call_claude(prompt, system_prompt)
            elif self.provider == "ollama":
                return self._call_ollama(prompt, system_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"LLM call failed ({self.provider}/{self.model}): {e}")
            raise

    def generate_json(self, prompt: str, system_prompt: str = "") -> dict:
        raw = self.generate(prompt, system_prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            first_nl = cleaned.find("\n")
            if first_nl != -1:
                cleaned = cleaned[first_nl:].strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start: end + 1])
                except json.JSONDecodeError:
                    pass
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start: end + 1])
                except json.JSONDecodeError:
                    pass
            logger.error(f"Failed to parse JSON: {cleaned[:200]}")
            return {"error": "Failed to parse JSON", "raw": cleaned[:500]}

    # ── Provider-specific calls ────────────────────────────────────────

    def _call_openai_compat(self, prompt: str, system_prompt: str) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=4096,
        )
        return resp.choices[0].message.content.strip()

    def _call_gemini(self, prompt: str, system_prompt: str) -> str:
        model = self._client.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt or None,
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()

    def _call_claude(self, prompt: str, system_prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.3,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        resp = self._client.messages.create(**kwargs)
        return resp.content[0].text.strip()

    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        import httpx
        from backend.app.config import settings

        base_url = settings.ollama_base_url
        url = f"{base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {"temperature": 0.3},
        }
        resp = httpx.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
