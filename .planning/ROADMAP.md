# Roadmap: imessage-ai

## Overview

This roadmap delivers a local-first CLI tool for querying iMessage history with AI, from foundational data access through advanced analytics and polished distribution. The journey follows natural technical dependencies: establish macOS data access, build offline indexing infrastructure, integrate LLM-powered query, enhance user experience, add differentiating insights, enable data export, and polish for public launch.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Project Setup & Foundation** - Python project scaffolding, development tooling, testing framework
- [ ] **Phase 2: Data Access Layer** - Read and parse macOS chat.db with all message types and contacts
- [ ] **Phase 3: Indexing Pipeline** - Generate embeddings, store in vector database, handle incremental updates
- [ ] **Phase 4: Query & LLM Integration** - Semantic search, RAG pipeline, local and cloud LLM support
- [ ] **Phase 5: CLI & REPL** - Interactive chat interface with commands, history, graceful error handling
- [ ] **Phase 6: Insights & Analytics** - Communication stats, relationship analysis, topic mapping, self-improvement suggestions
- [ ] **Phase 7: Export Functionality** - Export conversations to JSON, CSV, and Markdown with filtering
- [ ] **Phase 8: Distribution & Polish** - Homebrew formula, PyPI package, documentation, demo GIF, final optimizations

## Phase Details

### Phase 1: Project Setup & Foundation
**Goal**: Establish Python project structure with development tooling ready for implementation
**Depends on**: Nothing (first phase)
**Requirements**: None (infrastructure phase)
**Success Criteria** (what must be TRUE):
  1. Python project can be installed locally with `pip install -e .`
  2. Test suite runs successfully with pytest
  3. Code formatting and linting tools are configured and passing
  4. Project has clear directory structure for modules (data, index, query, cli, insights, export)
**Plans**: TBD

Plans:
- [ ] 01-01: TBD
- [ ] 01-02: TBD

### Phase 2: Data Access Layer
**Goal**: Successfully read and parse all message types from macOS chat.db with proper contact resolution
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07
**Success Criteria** (what must be TRUE):
  1. Tool reads messages from chat.db on macOS (both text field and attributedBody binary plist)
  2. Tool converts Apple epoch timestamps to human-readable dates correctly
  3. Tool resolves contact handles (phone, email) to display names
  4. Tool parses group chats including participant lists and group names
  5. Tool detects missing Full Disk Access permissions and provides clear setup instructions
  6. Tool handles WAL journal mode by safely copying database before reading
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Indexing Pipeline
**Goal**: Generate semantic embeddings of message history and store in vector database for retrieval
**Depends on**: Phase 2
**Requirements**: INDX-01, INDX-02, INDX-03, INDX-04, INDX-05
**Success Criteria** (what must be TRUE):
  1. Tool chunks messages by conversation and time window (preserves semantic context)
  2. Tool generates vector embeddings using local sentence-transformers model
  3. Tool stores embeddings in ChromaDB with metadata (sender, timestamp, chat_id, conversation type)
  4. Tool displays progress bar with ETA during indexing operations
  5. Tool supports incremental indexing (only processes new messages since last run)
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Query & LLM Integration
**Goal**: Enable natural language queries over message history with accurate, cited answers
**Depends on**: Phase 3
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, LLM-01, LLM-02, LLM-03, LLM-04
**Success Criteria** (what must be TRUE):
  1. User can ask natural language questions about their message history
  2. Tool performs semantic search to find relevant messages by meaning
  3. Tool maintains conversation context across multiple questions (sliding window)
  4. Tool streams LLM responses token-by-token in the terminal
  5. Tool cites source messages with sender, date, and conversation in answers
  6. Tool works with Ollama for fully local inference (no API keys required)
  7. User can configure OpenAI or Anthropic API keys for higher quality answers
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: CLI & REPL
**Goal**: Provide polished interactive chat experience with command support and robust error handling
**Depends on**: Phase 4
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, CLI-06, CLI-07
**Success Criteria** (what must be TRUE):
  1. Tool provides interactive REPL with prompt and command history
  2. User can start new conversation with `/clear` command
  3. User can resume previous conversation with `/resume` command
  4. Tool handles Ctrl-C gracefully without corrupting state
  5. `imessage-ai setup` command checks permissions, locates chat.db, runs initial index
  6. `imessage-ai chat` command starts interactive REPL
  7. `imessage-ai index` command triggers re-index (incremental by default, --full for complete)
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

### Phase 6: Insights & Analytics
**Goal**: Deliver proactive communication insights and relationship analytics beyond Q&A
**Depends on**: Phase 5
**Requirements**: INSI-01, INSI-02, INSI-03, INSI-04, INSI-05
**Success Criteria** (what must be TRUE):
  1. User can view basic message stats (total messages, messages per contact, date range, frequency)
  2. User can view relationship analytics (tone by person, conversation balance, response time patterns)
  3. User can view topic mapping (most discussed topics, trending topics over time)
  4. User can get self-improvement suggestions (tone analysis, communication patterns, actionable advice)
  5. Insights are accessible via CLI commands (e.g., `imessage-ai insights` or `/insights` in REPL)
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD

### Phase 7: Export Functionality
**Goal**: Enable users to export conversations in multiple formats with flexible filtering
**Depends on**: Phase 2
**Requirements**: EXPRT-01, EXPRT-02, EXPRT-03, EXPRT-04
**Success Criteria** (what must be TRUE):
  1. User can export conversations as JSON with full metadata
  2. User can export conversations as CSV for spreadsheet analysis
  3. User can export conversations as Markdown for readable archives
  4. User can filter exports by contact, date range, or conversation
**Plans**: TBD

Plans:
- [ ] 07-01: TBD

### Phase 8: Distribution & Polish
**Goal**: Package and document for public release via Homebrew and PyPI
**Depends on**: Phase 7
**Requirements**: DIST-01, DIST-02, DIST-03, DIST-04
**Success Criteria** (what must be TRUE):
  1. Tool is installable via Homebrew formula (`brew install imessage-ai`)
  2. Tool is installable via pip/pipx from PyPI
  3. README includes demo GIF, clear install steps, and architecture diagram
  4. User can go from install to first query in three commands or fewer
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Setup & Foundation | 0/TBD | Not started | - |
| 2. Data Access Layer | 0/TBD | Not started | - |
| 3. Indexing Pipeline | 0/TBD | Not started | - |
| 4. Query & LLM Integration | 0/TBD | Not started | - |
| 5. CLI & REPL | 0/TBD | Not started | - |
| 6. Insights & Analytics | 0/TBD | Not started | - |
| 7. Export Functionality | 0/TBD | Not started | - |
| 8. Distribution & Polish | 0/TBD | Not started | - |
