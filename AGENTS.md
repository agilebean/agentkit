# AgentKit

Shared infrastructure for AI agent projects on Apple Silicon.

## Modules

| Path | Purpose | Install |
|------|---------|---------|
| `agentkit.llm.litellm` | LLM abstraction via litellm | `[llm]` |
| `agentkit.speech.tts` | Kokoro text-to-speech | `[speech]` |
| `agentkit.speech.stt` | Parakeet speech-to-text | `[speech]` |
| `agentkit.speech.audio_io` | Mic recording + speaker playback | `[audio]` |
| `agentkit.gmail.client` | Gmail API (OAuth, fetch, search) | `[gmail]` |
| `agentkit.gmail.query` | Gmail search query builder | `[gmail]` |
| `agentkit.notify.push` | Push notifications (ntfy.sh) | `[notify]` |
| `agentkit.imap.collector` | IMAP email collector | `[imap]` |
| `agentkit.prompts.loader` | Markdown prompt loader | (stdlib) |
| `agentkit.sqlite_store` | SQLite store base class | (stdlib) |
| `agentkit.common` | repo_root(), CSV/MD writers | (stdlib) |
| `agentkit.config` | YAML config + env override | (stdlib + pyyaml) |
| `agentkit.errors` | AgentError, LLMFailureWithTranscript | (stdlib) |

All modules are Apple Silicon only. MLX-dependent modules require macOS with M-series chip.
