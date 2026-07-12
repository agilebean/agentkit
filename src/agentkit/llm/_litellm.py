"""Cloud LLM abstraction via direct HTTP to OpenAI-compatible endpoints.

All endpoints (opencode go proxy, direct DeepSeek, LM Studio) speak the
OpenAI chat completions API format, so litellm's multi-provider normalization
is not needed. Uses stdlib urllib.request instead.

For local MLX models see ``agentkit.llm.mlx``.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from agentkit.core import LLMError

# ---------------------------------------------------------------------------
# Default model aliases (overridable per project)
# ---------------------------------------------------------------------------

DEFAULT_MODEL_ALIASES: dict[str, str] = {
    "fast": "deepseek/deepseek-v4-flash",
    "smart": "deepseek/deepseek-v4-pro",
    "local": "openai/local-model",
    "local_smart": "openai/local-model",
    "cheap": "openai/minimax-m2.5",
}

# Aliases routed through OpenCode Go API (OpenAI-compatible endpoint)
_GO_API_ALIASES = frozenset({"fast", "smart", "cheap"})

# LM Studio defaults for local aliases
_LM_STUDIO_BASE_URL = os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
_LOCAL_MODEL_DEFAULT = "mlx-community/Qwen3.5-4B-MLX-4bit"

# ---------------------------------------------------------------------------
# Auth resolution
# ---------------------------------------------------------------------------

_AUTH_PATH = Path.home() / ".local" / "share" / "opencode" / "auth.json"


def _read_auth_json() -> dict:
    if not _AUTH_PATH.is_file():
        return {}
    try:
        return json.loads(_AUTH_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _get_go_api_key() -> str | None:
    """Return the OpenCode Go API subscription key, or ``None`` if unavailable.

    Priority:
    1. ``OPENCODE_API_KEY`` env var
    2. auth.json -> ``opencode``, ``opencode-go``, ``zen``, ``opencode-zen`` blocks
    """
    key = os.environ.get("OPENCODE_API_KEY", "").strip()
    if key:
        return key

    data = _read_auth_json()
    for block in ("opencode", "opencode-go", "zen", "opencode-zen"):
        entry = data.get(block)
        if isinstance(entry, dict):
            k = entry.get("key") or entry.get("apiKey")
            if isinstance(k, str) and k.strip():
                return k.strip()
    return None


def _get_personal_deepseek_key() -> str | None:
    """Return the personal DeepSeek API key, or ``None`` if unavailable.

    Priority:
    1. auth.json -> ``deepseek`` block
    2. ``DEEPSEEK_API_KEY`` env var
    """
    data = _read_auth_json()
    entry = data.get("deepseek")
    if isinstance(entry, dict):
        k = entry.get("key")
        if isinstance(k, str) and k.strip():
            return k.strip()

    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    return None


# Public aliases (consumers import these instead of re-implementing auth readers)
get_go_api_key = _get_go_api_key
get_personal_deepseek_key = _get_personal_deepseek_key


# ---------------------------------------------------------------------------
# Model alias resolution
# ---------------------------------------------------------------------------

def resolve_model(
    alias: str,
    *,
    aliases: dict[str, str] | None = None,
) -> str:
    """Resolve a model alias to a provider model ID.

    Environment variable ``{ALIAS.upper()}_MODEL`` overrides the alias lookup.
    If *aliases* is provided it is used instead of ``DEFAULT_MODEL_ALIASES``.
    """
    alias_map = aliases or DEFAULT_MODEL_ALIASES
    env_key = f"{alias.upper()}_MODEL"
    env_val = os.environ.get(env_key, "").strip()
    if env_val:
        return env_val
    return alias_map.get(alias, alias)


# ---------------------------------------------------------------------------
# HTTP transport (mockable seam)
# ---------------------------------------------------------------------------

_HTTP_TIMEOUT_S = 120


def _strip_provider_prefix(model: str) -> str:
    """Strip litellm-style provider prefix (e.g. 'deepseek/deepseek-v4-flash' -> 'deepseek-v4-flash')."""
    if "/" in model:
        return model.split("/", 1)[1]
    return model


def _wrap_tool_calls(tool_calls: list | None) -> list:
    if not tool_calls:
        return []
    result = []
    for tc in tool_calls:
        if isinstance(tc, dict):
            fn = tc.get("function", {})
            result.append(SimpleNamespace(
                id=tc.get("id", ""),
                type=tc.get("type", "function"),
                function=SimpleNamespace(
                    name=fn.get("name", ""),
                    arguments=fn.get("arguments", ""),
                ),
            ))
        else:
            result.append(tc)
    return result


def _wrap_response(data: dict) -> SimpleNamespace:
    """Wrap OpenAI JSON response in SimpleNamespace for attribute access."""
    choices = []
    for c in data.get("choices", []):
        msg = c.get("message", {})
        message = SimpleNamespace(
            role=msg.get("role", "assistant"),
            content=msg.get("content"),
            tool_calls=_wrap_tool_calls(msg.get("tool_calls")),
        )
        choices.append(SimpleNamespace(
            message=message,
            finish_reason=c.get("finish_reason"),
            index=c.get("index", 0),
        ))

    usage_data = data.get("usage") or {}
    usage = SimpleNamespace(
        prompt_tokens=usage_data.get("prompt_tokens", 0),
        completion_tokens=usage_data.get("completion_tokens", 0),
        total_tokens=usage_data.get("total_tokens", 0),
    )

    return SimpleNamespace(choices=choices, usage=usage, id=data.get("id", ""))


def _post_completion(**kwargs: Any) -> SimpleNamespace:
    """Make an OpenAI-compatible chat completion HTTP request.

    This is the mockable seam for tests. Returns a SimpleNamespace wrapping
    the JSON response with attribute access for .choices, .usage, etc.
    """
    api_base = kwargs.pop("api_base", "https://api.openai.com/v1")
    api_key = kwargs.pop("api_key", "")

    request_model = kwargs.get("model", "")
    kwargs["model"] = _strip_provider_prefix(request_model)

    url = f"{api_base.rstrip('/')}/chat/completions"
    body = json.dumps(kwargs).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {error_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection failed: {e.reason}") from e

    response = _wrap_response(data)
    response.model = request_model
    return response


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------

# USD per million tokens: (input_price, output_price).
# Add entries here as needed; unknown models default to 0.0.
_PRICING: dict[str, tuple[float, float]] = {}


def _estimate_cost(model: str, usage: Any) -> float:
    """Estimate USD cost from token counts and model pricing."""
    if usage is None:
        return 0.0
    pricing = _PRICING.get(model)
    if pricing is None:
        return 0.0
    try:
        input_per_token = pricing[0] / 1_000_000
        output_per_token = pricing[1] / 1_000_000
        prompt = getattr(usage, "prompt_tokens", 0) or 0
        completion = getattr(usage, "completion_tokens", 0) or 0
        return float(prompt * input_per_token + completion * output_per_token)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Core completion
# ---------------------------------------------------------------------------

LogFn = Callable[[dict[str, Any]], None]


def complete(
    messages: list[dict[str, Any]],
    alias: str = "smart",
    *,
    max_tokens: int = 2000,
    temperature: float = 0.3,
    json_mode: bool = False,
    aliases: dict[str, str] | None = None,
    log_fn: LogFn | None = None,
    **extra_kwargs: Any,
) -> str:
    """Send a chat completion request. Returns the response text.

    Auth is resolved automatically with fallback: opencode subscription
    key first, then personal DeepSeek API key. The source is printed to stdout.

    Args:
        messages: Chat messages in OpenAI format.
        alias: Model alias (``fast``, ``smart``, ``cheap``, ``local``, etc.).
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature (0.0-1.0).
        json_mode: If True, request JSON object response format.
        aliases: Override ``DEFAULT_MODEL_ALIASES`` per project.
        log_fn: Optional callback ``log_fn(record)`` called after completion.
        **extra_kwargs: Passed directly to the API as JSON body fields.

    Returns:
        Generated text string.

    Raises:
        LLMError: On any HTTP or auth failure.
    """
    model = resolve_model(alias, aliases=aliases)
    t0 = time.perf_counter()
    error_msg: str | None = None

    try:
        kwargs = _build_completion_kwargs(
            model=model,
            alias=alias,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=json_mode,
            **extra_kwargs,
        )
        try:
            resp = _post_completion(**kwargs)
        except Exception:
            if kwargs.get("api_base") and "go/v1" in str(kwargs.get("api_base", "")):
                fallback_key = _get_personal_deepseek_key()
                if fallback_key and fallback_key != kwargs.get("api_key"):
                    print(
                        "Go API request failed, falling back to direct DeepSeek API.",
                        file=sys.stderr,
                    )
                    kwargs.pop("api_base", None)
                    kwargs["api_key"] = fallback_key
                    kwargs["api_base"] = os.environ.get(
                        "DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"
                    )
                    resp = _post_completion(**kwargs)
                else:
                    raise
            else:
                raise
    except Exception as e:
        error_msg = str(e)
        raise LLMError(error_msg) from e
    finally:
        if log_fn:
            duration_ms = (time.perf_counter() - t0) * 1000
            usage: dict[str, int] = {}
            cost = 0.0
            if error_msg is None:
                try:
                    usage = {
                        "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                        "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
                        "total_tokens": getattr(resp.usage, "total_tokens", 0) or 0,
                    }
                except Exception:
                    pass
                try:
                    cost = _estimate_cost(model, resp.usage)
                except Exception:
                    pass
            log_fn(
                {
                    "alias": alias,
                    "model": model,
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                    "cost_usd": cost,
                    "duration_ms": duration_ms,
                    "error": error_msg,
                }
            )

    return str(resp.choices[0].message.content or "")


def complete_with_tools(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    tool_choice: str = "auto",
    alias: str = "smart",
    *,
    max_tokens: int = 2000,
    temperature: float = 0.3,
    aliases: dict[str, str] | None = None,
    log_fn: LogFn | None = None,
    **extra_kwargs: Any,
) -> Any:
    """Send a chat completion request with tool definitions.

    Returns the raw response object. Consumers parse tool calls themselves.

    Args:
        messages: Chat messages in OpenAI format.
        tools: List of OpenAI function tool definitions.
        tool_choice: ``"auto"``, ``"none"``, or a specific tool dict.
        alias: Model alias.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        aliases: Override ``DEFAULT_MODEL_ALIASES``.
        log_fn: Optional callback.
        **extra_kwargs: Passed to the API as JSON body fields.

    Returns:
        Raw response object (SimpleNamespace with .choices, .usage, .model).
    """
    model = resolve_model(alias, aliases=aliases)

    try:
        kwargs = _build_completion_kwargs(
            model=model,
            alias=alias,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **extra_kwargs,
        )
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice
        return _post_completion(**kwargs)
    except Exception as e:
        raise LLMError(str(e)) from e


def response_cost_usd(response: Any) -> float:
    """Estimate USD cost of a completion response."""
    try:
        model = getattr(response, "model", "")
        usage = getattr(response, "usage", None)
        return _estimate_cost(model, usage)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_completion_kwargs(
    *,
    model: str,
    alias: str,
    messages: list[dict[str, Any]],
    max_tokens: int,
    temperature: float,
    json_mode: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        **extra,
    }

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    # LM Studio local models
    if alias in ("local", "local_smart"):
        kwargs["api_base"] = _LM_STUDIO_BASE_URL
        kwargs["api_key"] = os.environ.get("LM_STUDIO_API_KEY", "lm-studio")
        return kwargs

    # Cloud models via OpenCode Go API (subscription) or direct DeepSeek (personal key)
    if alias in _GO_API_ALIASES or "deepseek" in model.lower():
        go_key = _get_go_api_key()
        if go_key:
            kwargs["api_key"] = go_key
            kwargs["api_base"] = os.environ.get(
                "OPENCODE_API_BASE", "https://opencode.ai/zen/go/v1"
            )
        else:
            personal_key = _get_personal_deepseek_key()
            if personal_key:
                kwargs["api_key"] = personal_key
                kwargs["api_base"] = os.environ.get(
                    "DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"
                )
            else:
                raise LLMError(
                    "No DeepSeek API key found. Add it under 'opencode' or 'deepseek' blocks in "
                    "~/.local/share/opencode/auth.json, or set DEEPSEEK_API_KEY / OPENCODE_API_KEY env var."
                )
        return kwargs

    return kwargs
