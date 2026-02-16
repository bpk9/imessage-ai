# Requirements: imessage-ai

**Defined:** 2026-02-16
**Core Value:** Users can ask natural language questions about their iMessage history and get accurate, contextual answers — all running locally on their Mac.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Access

- [ ] **DATA-01**: Tool can read and parse all message types from macOS chat.db SQLite database
- [ ] **DATA-02**: Tool correctly handles Apple epoch timestamps (nanoseconds since 2001-01-01)
- [ ] **DATA-03**: Tool parses attributedBody encoding on macOS Ventura+ (binary plist format)
- [ ] **DATA-04**: Tool resolves contact handles (phone numbers, emails) to display names
- [ ] **DATA-05**: Tool handles group chats including participant lists and group names
- [ ] **DATA-06**: Tool handles WAL journal mode by copying chat.db before reading
- [ ] **DATA-07**: Tool detects and guides user through Full Disk Access permission setup

### Indexing

- [ ] **INDX-01**: Tool chunks messages by conversation and time window (not fixed-size) for semantic coherence
- [ ] **INDX-02**: Tool generates vector embeddings using local sentence-transformers (all-MiniLM-L6-v2)
- [ ] **INDX-03**: Tool stores embeddings in ChromaDB with metadata (sender, timestamp, chat_id, conversation type)
- [ ] **INDX-04**: Tool shows progress bar with ETA during indexing
- [ ] **INDX-05**: Tool supports incremental indexing (only process new messages since last run)

### Search & Chat

- [ ] **CHAT-01**: User can ask natural language questions about their message history
- [ ] **CHAT-02**: Tool performs semantic search to find messages by meaning, not just keywords
- [ ] **CHAT-03**: Tool maintains multi-turn conversation context (sliding window of recent Q&A pairs)
- [ ] **CHAT-04**: Tool streams LLM responses token-by-token in the terminal
- [ ] **CHAT-05**: Tool cites source messages with sender, date, and conversation in answers

### CLI Experience

- [ ] **CLI-01**: Tool provides interactive chat REPL with prompt and command history
- [ ] **CLI-02**: User can start new conversation with `/clear` command
- [ ] **CLI-03**: User can resume previous conversation with `/resume` command
- [ ] **CLI-04**: Tool handles Ctrl-C gracefully without corrupting state
- [ ] **CLI-05**: `imessage-ai setup` command checks permissions, locates chat.db, runs initial index
- [ ] **CLI-06**: `imessage-ai chat` command starts interactive REPL
- [ ] **CLI-07**: `imessage-ai index` command triggers re-index (incremental by default, --full for complete)

### LLM Integration

- [ ] **LLM-01**: Tool works with Ollama for fully local inference (no API keys required)
- [ ] **LLM-02**: User can opt-in to OpenAI API for better quality answers
- [ ] **LLM-03**: User can opt-in to Anthropic Claude API for better quality answers
- [ ] **LLM-04**: Tool uses RAG pipeline: embed query → retrieve relevant chunks → construct prompt → generate answer

### Insights

- [ ] **INSI-01**: User can view basic message stats (total messages, messages per contact, date range, frequency)
- [ ] **INSI-02**: User can view relationship analytics (tone by person, conversation balance, response time patterns)
- [ ] **INSI-03**: User can view topic mapping (most discussed topics, trending topics over time)
- [ ] **INSI-04**: User can get self-improvement suggestions (tone analysis, communication patterns, actionable advice)
- [ ] **INSI-05**: Insights are accessible via CLI commands (e.g., `imessage-ai insights` or `/insights` in REPL)

### Export

- [ ] **EXPRT-01**: User can export conversations as JSON
- [ ] **EXPRT-02**: User can export conversations as CSV
- [ ] **EXPRT-03**: User can export conversations as Markdown
- [ ] **EXPRT-04**: User can filter exports by contact, date range, or conversation

### Distribution

- [ ] **DIST-01**: Tool is installable via Homebrew formula
- [ ] **DIST-02**: Tool is installable via pip/pipx from PyPI
- [ ] **DIST-03**: README includes demo GIF, clear install steps, and architecture diagram
- [ ] **DIST-04**: Three commands or fewer from install to first query

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Search Enhancements

- **SRCH-01**: User can filter search results by contact, date range, or group chat
- **SRCH-02**: Tool supports hybrid search combining semantic and keyword matching (better for names, acronyms)

### CLI Enhancements

- **CLIX-01**: REPL provides tab-completion and autocomplete for commands
- **CLIX-02**: Terminal visualization with ASCII charts for insights data

### Advanced Insights

- **AINSI-01**: User can view sentiment analysis over time (emotional arc of relationships)
- **AINSI-02**: User can view group chat dynamics (who dominates, response patterns, subgroups)
- **AINSI-03**: User can view conversation summarization (quick overview of long threads)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Web UI | CLI-only for v1, keeps scope tight and ships faster |
| Real-time message monitoring | Privacy concerns, complexity, battery drain — batch analysis only |
| Cloud storage of messages | Privacy violation, against core value prop |
| Message sending | Read-only tool, security risk, out of scope |
| Custom embeddings training | Overkill for personal-scale data |
| Multi-platform support | iMessage is macOS-only, chat.db is Mac-specific |
| GUI configuration | CLI tool, JSON config file is sufficient |
| Automated posting/sharing | Privacy risk, user controls what leaves the tool |
| Plugin system | Premature for v1 launch |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | — | Pending |
| DATA-02 | — | Pending |
| DATA-03 | — | Pending |
| DATA-04 | — | Pending |
| DATA-05 | — | Pending |
| DATA-06 | — | Pending |
| DATA-07 | — | Pending |
| INDX-01 | — | Pending |
| INDX-02 | — | Pending |
| INDX-03 | — | Pending |
| INDX-04 | — | Pending |
| INDX-05 | — | Pending |
| CHAT-01 | — | Pending |
| CHAT-02 | — | Pending |
| CHAT-03 | — | Pending |
| CHAT-04 | — | Pending |
| CHAT-05 | — | Pending |
| CLI-01 | — | Pending |
| CLI-02 | — | Pending |
| CLI-03 | — | Pending |
| CLI-04 | — | Pending |
| CLI-05 | — | Pending |
| CLI-06 | — | Pending |
| CLI-07 | — | Pending |
| LLM-01 | — | Pending |
| LLM-02 | — | Pending |
| LLM-03 | — | Pending |
| LLM-04 | — | Pending |
| INSI-01 | — | Pending |
| INSI-02 | — | Pending |
| INSI-03 | — | Pending |
| INSI-04 | — | Pending |
| INSI-05 | — | Pending |
| EXPRT-01 | — | Pending |
| EXPRT-02 | — | Pending |
| EXPRT-03 | — | Pending |
| EXPRT-04 | — | Pending |
| DIST-01 | — | Pending |
| DIST-02 | — | Pending |
| DIST-03 | — | Pending |
| DIST-04 | — | Pending |

**Coverage:**
- v1 requirements: 37 total
- Mapped to phases: 0
- Unmapped: 37 ⚠️

---
*Requirements defined: 2026-02-16*
*Last updated: 2026-02-16 after initial definition*
