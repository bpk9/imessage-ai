# imessage-ai

## What This Is

A CLI tool that lets you chat with your iMessage history using AI. It reads the local `chat.db` SQLite database on macOS, indexes conversations, and provides an interactive chat REPL for natural language questions about your messages — plus insight commands that analyze your communication patterns. Designed for Hacker News launch: open-source, privacy-first, beautifully polished.

## Core Value

Users can ask natural language questions about their iMessage history and get accurate, contextual answers — all running locally on their Mac.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Parse and index iMessage chat.db (all message types, contacts, group chats)
- [ ] Interactive chat REPL with persistent conversation context (like Ollama/Claude Code)
- [ ] Semantic search — find messages by meaning, not just keywords
- [ ] REPL commands: `/clear` (new conversation), `/resume` (pick up old thread)
- [ ] Local-first: Ollama for LLM, local embeddings, no API keys required for default setup
- [ ] Cloud LLM opt-in (OpenAI/Anthropic) for better quality answers
- [ ] Insight: Communication stats (most texted, busiest hours, response times, volume trends)
- [ ] Insight: Relationship analysis (tone by person, conversation depth, closeness)
- [ ] Insight: Topic mapping (what you talk about most, trending topics over time)
- [ ] Insight: Self-improvement (tone analysis, communication patterns, improvement suggestions)
- [ ] Incremental indexing (only process new messages on re-index)
- [ ] Simple setup: `imessage-ai setup` → `imessage-ai chat`
- [ ] Homebrew formula for easy installation
- [ ] Polished README with demo GIF, clear install steps, architecture diagram

### Out of Scope

- Web UI — CLI-only for v1, keeps scope tight and ships faster
- Mobile app — macOS only (chat.db is Mac-only)
- Conversation browser UI — not needed in CLI-first approach
- Real-time sync / daemon — manual indexing for v1
- Multi-Mac sync — single machine for v1
- Plugin system — premature for launch

## Context

- macOS stores all iMessage history in `~/Library/Messages/chat.db` (SQLite)
- Requires Full Disk Access permission to read chat.db
- Apple date format: nanoseconds since 2001-01-01 epoch
- Key tables: `message`, `handle`, `chat`, `chat_handle_join`, `chat_message_join`
- No existing open-source tool does this well — first-mover opportunity
- Target: HN "Show HN" launch with broad appeal (devs + privacy-conscious users + Mac power users)
- The chat REPL UX is inspired by Ollama CLI and Claude Code — persistent conversation, slash commands

## Constraints

- **Platform**: macOS only — chat.db is a Mac-specific SQLite database
- **Privacy**: Must work fully offline by default. Cloud LLM is opt-in only.
- **Setup simplicity**: Three commands max from install to first query
- **Open source**: MIT license for maximum adoption

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI-only (no web UI) | Simpler scope, ships faster, fits the "developer tool" audience | — Pending |
| Local-first with cloud opt-in | Privacy is a key selling point but pragmatic about quality | — Pending |
| REPL-style chat (not one-shot) | Matches user mental model of conversation, enables follow-ups | — Pending |
| Insights as first-class feature | Differentiator vs generic "chat with docs" tools | — Pending |

---
*Last updated: 2026-02-15 after initialization*
