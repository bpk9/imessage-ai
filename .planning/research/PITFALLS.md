# Domain Pitfalls

**Domain:** Local iMessage AI CLI Tool (chat.db parsing + RAG + CLI REPL)
**Researched:** 2026-02-16

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: AttributedBody Encoding on Ventura+
**What goes wrong:** On macOS Ventura and later, message text is no longer stored in the `text` column but instead encoded as a binary blob in the `attributedBody` field. Standard SQL queries return NULL for most messages, making your tool appear broken or showing only partial message history.

**Why it happens:** Apple changed the storage format in Ventura without documentation. The `attributedBody` contains an Objective-C serialized object with binary plist data. Developers assume SQL text queries will work across all macOS versions.

**Consequences:**
- Tool shows incomplete message history
- Users lose trust when "recent messages are missing"
- Silent data loss if not detected during development
- Requires complete rewrite of message extraction logic

**Prevention:**
- Check BOTH `text` and `attributedBody` columns for every message
- Implement binary plist parsing using Python's `plistlib`
- Parse the hex blob: extract message content from the serialized object
- Test on Ventura, Sonoma, and latest macOS versions
- Expect this format to continue in future macOS releases

**Detection:**
- Run SQL query: `SELECT COUNT(*) FROM message WHERE text IS NULL AND attributedBody IS NOT NULL`
- If count > 0, you MUST parse attributedBody
- Test with messages sent from Ventura+ devices specifically

**Phase impact:** Must be addressed in Phase 1 (initial parsing). Cannot defer.

**Sources:**
- [iMessage Tools - Ventura AttributedBody](https://github.com/my-other-github-account/imessage_tools)
- [LangChain Issue #10680 - Schema Change](https://github.com/langchain-ai/langchain/issues/10680)

---

### Pitfall 2: Fixed-Size Chunking Destroys Semantic Meaning
**What goes wrong:** Using fixed-size chunks (e.g., 512 tokens) splits sentences, procedural steps, or safety qualifiers across chunk boundaries. RAG retrieves partial context like "don't" in one chunk and the action in another, returning misleading or incomplete answers.

**Why it happens:** Fixed-size chunking is the easiest to implement and many tutorials start there. Developers prioritize simplicity over quality, not realizing the semantic impact.

**Consequences:**
- Up to 9% gap in recall performance vs semantic chunking
- Context fragmentation makes answers incoherent
- Critical information split across chunks may never be retrieved together
- Users get wrong answers, especially for multi-turn conversations
- Hard to debug because some queries work fine while others fail mysteriously

**Prevention:**
- Use semantic chunking that groups messages by conversation context
- For iMessage: chunk by conversation thread or time-based sessions (e.g., messages within 30 minutes)
- Implement 10-20% overlap between chunks to prevent boundary loss
- Never split mid-sentence or mid-conversation turn
- Test chunking with long conversations and verify retrieved context quality

**Detection:**
- User questions about recent conversations return old messages
- Answers reference partial context without full statement
- Retrieval evaluation shows low recall on conversation-based queries
- Manual inspection shows chunks ending mid-sentence

**Phase impact:** Must be decided in Phase 2 (RAG implementation). Wrong choice forces rewrite when quality issues emerge.

**Sources:**
- [Best Chunking Strategies for RAG 2025](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025)
- [Document Chunking for RAG - 70% Accuracy Boost](https://langcopilot.com/posts/2025-10-11-document-chunking-for-rag-practical-guide)
- [Databricks Chunking Guide](https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089)

---

### Pitfall 3: Full Disk Access Permission Failures
**What goes wrong:** Tool fails with "Operation not permitted" when trying to read `~/Library/Messages/chat.db`. Users don't understand why it doesn't work, blame the tool, and abandon it.

**Why it happens:** macOS requires explicit Full Disk Access permission for any app reading chat.db. The database is protected by System Integrity Protection (SIP). Terminal/iTerm/Python must be granted FDA in System Settings.

**Consequences:**
- Tool appears completely broken on first run
- Users don't know they need to grant permissions manually
- No clear error message if not handled properly
- Homebrew-installed tools have additional complexity (user must grant FDA to their shell)
- Support burden explaining permissions to non-technical users

**Prevention:**
- Check access before attempting to read: `SELECT COUNT(*) FROM message LIMIT 1`
- Catch permission errors explicitly and provide clear instructions
- Display step-by-step permission grant instructions with screenshots
- Detect which shell/terminal is running and provide specific guidance
- Warn users that SIP must remain enabled (never suggest disabling SIP)
- Document that FDA is required, not optional

**Detection:**
- `sqlite3.OperationalError: unable to open database file`
- `sqlite3.OperationalError: authorization denied`
- File exists at path but cannot be opened
- Works in one terminal but not another (FDA granted to specific app)

**Phase impact:** Must be handled in Phase 1 (initial access). Critical for first-run experience.

**Sources:**
- [Operation Not Permitted Error on Mac](https://umatechnology.org/operation-not-permitted-error-on-mac-heres-how-to-fix-it-mactips/)
- [Explainer: Permissions, Privacy and TCC](https://eclecticlight.co/2025/11/08/explainer-permissions-privacy-and-tcc/)
- [What Is System Integrity Protection on Mac](https://www.cleverfiles.com/help/system-integrity-protection.html)

---

### Pitfall 4: WAL Journal Mode Breaks Read-Only Access
**What goes wrong:** Opening chat.db in read-only mode fails because the database uses WAL (Write-Ahead Logging) journal mode, which requires write access to `.sqlite-wal` files. Tool crashes or shows incomplete data.

**Why it happens:** macOS Messages app uses WAL mode by default for performance. WAL requires creating/updating journal files even for read operations. Developers assume read-only mode works universally.

**Consequences:**
- Cannot safely read database while Messages app is running
- "Database is locked" errors
- Incomplete data if WAL checkpoint hasn't been applied
- Race conditions if Messages app writes during read
- Data corruption risk if both processes access simultaneously

**Prevention:**
- Do NOT open in read-only mode with WAL active
- Copy chat.db to temporary location and convert to DELETE journal mode:
  ```python
  import shutil
  import sqlite3

  # Copy database
  shutil.copy('~/Library/Messages/chat.db', '/tmp/chat.db')

  # Convert to DELETE mode
  conn = sqlite3.connect('/tmp/chat.db')
  conn.execute('PRAGMA journal_mode=DELETE')
  conn.close()
  ```
- Always work on a copy, never the live database
- Check journal mode: `PRAGMA journal_mode;`
- Document that Messages app should be closed during initial indexing

**Detection:**
- Error: "unable to open database file" with WAL files present
- SQLITE_READONLY errors
- Missing recent messages (WAL not checkpointed)
- File lock errors

**Phase impact:** Must be handled in Phase 1 (database access). Affects reliability and data completeness.

**Sources:**
- [Write-Ahead Logging - SQLite](https://sqlite.org/wal.html)
- [Journal Modes in SQLite](https://blog.sqlite.ai/journal-modes-in-sqlite)
- [Enabling WAL Mode](https://til.simonwillison.net/sqlite/enabling-wal-mode)

---

### Pitfall 5: Embedding Model Changes Break Existing Index
**What goes wrong:** Upgrading or changing the embedding model after users have indexed their messages means the new query embeddings exist in a different vector space than the stored message embeddings. Retrieval returns completely irrelevant results.

**Consequences:**
- Users must re-index entire message history (time-consuming)
- Previous embeddings become worthless
- No incremental upgrade path
- Breaking change in every update if not planned
- User frustration with slow re-indexing

**Prevention:**
- Store embedding model name and version with the index
- Check model compatibility on startup
- Auto-detect when re-indexing is required
- Provide clear migration path with progress indication
- Consider model stability in initial selection
- Use established models less likely to change (e.g., OpenAI text-embedding-3-small)
- Document that model changes are breaking changes

**Detection:**
- Queries return obviously wrong results after update
- Semantic similarity scores are nonsensical
- Model metadata mismatch between index and current config

**Phase impact:** Must be designed in Phase 2 (embedding infrastructure). Cannot retrofit easily.

**Sources:**
- [Three Mistakes When Introducing Embeddings](https://bergum.medium.com/four-mistakes-when-introducing-embeddings-and-vector-search-d39478a568c5)
- [When Good Models Go Bad](https://weaviate.io/blog/when-good-models-go-bad)

---

### Pitfall 6: Python Homebrew Formula Requires Source Distributions
**What goes wrong:** Homebrew formula installation fails because dependencies lack source distributions (sdist) on PyPI. Build errors appear for users despite working locally.

**Why it happens:** Homebrew requires ALL dependencies (recursively) to have sdist available, not just wheels. Many modern Python packages only publish wheels. `homebrew-pypi-poet` generates formulas that include every installed package, including dev dependencies if not using a clean venv.

**Consequences:**
- Cannot publish to homebrew-core
- Installation fails for users
- Must maintain manual dependency list
- Version pinning becomes fragile
- Support burden for installation issues

**Prevention:**
- Verify sdist exists for EVERY dependency: `pip download --no-binary :all: <package>`
- Generate formula in a CLEAN virtualenv: no extra packages installed
- Explicitly declare all resources in formula (don't rely on automatic resolution)
- Test formula in fresh environment before publishing
- Follow PEP 668 for Python 3.12+: install in libexec virtualenv
- Choose dependencies that publish sdist, not just wheels
- Add license to package (required for homebrew-core)

**Detection:**
- `homebrew-pypi-poet` includes unexpected packages
- Formula installation fails with "no sdist available"
- Users report installation errors that don't reproduce locally
- Build fails on CI but not on dev machine

**Phase impact:** Must be considered in Phase 5 (distribution). Late discovery forces dependency changes.

**Sources:**
- [Packaging a Python CLI Tool for Homebrew](https://til.simonwillison.net/homebrew/packaging-python-cli-for-homebrew)
- [Python for Formula Authors - Homebrew](https://docs.brew.sh/Python-for-Formula-Authors)
- [Publishing Python CLI Tool to Homebrew](https://safjan.com/publishing-python-cli-tool-to-homebrew/)

---

## Moderate Pitfalls

### Pitfall 7: Context Window Degradation ("Lost in the Middle")
**What goes wrong:** Stuffing too many retrieved messages into the LLM context window causes the model to ignore middle content, focusing only on the beginning and end. Recall degrades as context grows.

**Prevention:**
- Implement reranking to surface most relevant messages
- Use hybrid search (BM25 + vector) for better initial retrieval
- Limit retrieved context to top 5-10 most relevant messages
- Employ sliding window or summarization for very long conversations
- Monitor context size and warn when approaching limits
- Consider conversation summarization for history beyond immediate context

**Detection:**
- Answers ignore relevant information from middle of retrieved context
- Quality degrades with more retrieved messages (counterintuitive)
- Users report "it didn't see the message I was asking about"

**Phase impact:** Must be addressed in Phase 3 (LLM integration). Quality issue that compounds over time.

**Sources:**
- [Context Window Management Strategies](https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/)
- [RAG Review 2025: From RAG to Context](https://ragflow.io/blog/rag-review-2025-from-rag-to-context)
- [LLM Context Management Guide](https://eval.16x.engineer/blog/llm-context-management-guide)

---

### Pitfall 8: Group Chat Name Resolution Failures
**What goes wrong:** Group chats don't have stable names in chat.db. Names can be NULL, different across devices, or change over time. Tool shows "Unknown Group" or wrong names, making conversations hard to identify.

**Prevention:**
- Handle NULL group chat names gracefully
- Extract participant names from `chat_handle_join` table
- Generate display name from participants: "Alice, Bob, Charlie"
- Store user-friendly aliases for group chats
- Detect when group chat was renamed on Mac vs iPhone (Mac-renamed groups have different behavior)
- Don't rely on `display_name` column alone

**Detection:**
- Queries show "Unknown" for group chats
- Same conversation appears under different names
- Group chat messages not attributed correctly

**Phase impact:** Addressed in Phase 1 (parsing). Affects UX but not critical functionality.

**Sources:**
- [iMessage Tools - Group Chat Naming](https://github.com/my-other-github-account/imessage_tools)
- [Analyzing iMessage Conversations](https://stmorse.github.io/journal/iMessage.html)

---

### Pitfall 9: Handle ID Mapping Complexity
**What goes wrong:** A single contact can have multiple handle IDs (phone number, email, multiple emails). Messages from the same person appear as different people if handles aren't unified.

**Prevention:**
- Join `message` → `handle` → contacts database
- Map multiple handles to single contact entity
- Handle cases where contact info isn't in address book
- Display phone/email if no contact name available
- Account for handle changes (user switches email/phone)

**Detection:**
- Same person appears as multiple distinct contacts
- Conversation fragmentation by handle
- Search for person's name misses some messages

**Phase impact:** Addressed in Phase 1 (parsing). Affects search quality and UX.

**Sources:**
- [Searching iMessage Database with SQL](https://spin.atomicobject.com/search-imessage-sql/)
- [Extract iMessage and Address Book Data](https://betterprogramming.pub/extracting-imessage-and-address-book-data-b6e2e5729b21)

---

### Pitfall 10: Deleted Messages Still in Database
**What goes wrong:** "Deleted" messages remain in chat.db with flags marking them as deleted, but aren't actually removed. Tool surfaces deleted messages users expect to be gone, violating expectations and privacy.

**Prevention:**
- Check message flags/status for deletion markers
- Filter deleted messages unless explicitly requested
- Respect the 30-day Recently Deleted retention window
- Provide option to include/exclude deleted messages
- Document that deletion doesn't remove from database

**Detection:**
- Users see messages they deleted
- Message count doesn't match Messages app display
- Privacy complaints about surfacing deleted content

**Phase impact:** Addressed in Phase 1 (parsing). Important for privacy expectations.

**Sources:**
- [How to Recover chat.db Deleted Messages](https://www.easeus.com/mac-file-recovery/chatdb-deleted-messages.html)
- [Searching iMessage Database with SQL](https://spin.atomicobject.com/search-imessage-sql/)

---

### Pitfall 11: Local Embedding Performance at Scale
**What goes wrong:** Embedding 100K+ messages locally takes hours with slower models, making initial indexing painful and incremental updates slow. Users abandon tool during long first-run.

**Prevention:**
- Use lightweight models optimized for on-device use (e.g., EmbeddingGemma - 200MB RAM with quantization)
- Show progress bar with ETA during indexing
- Implement batching to process messages in chunks
- Cache embeddings aggressively
- Support incremental indexing (only new messages)
- Provide estimated time based on message count
- Consider smaller models (e5-small: 16ms latency, 14x faster than large models)

**Detection:**
- Initial indexing takes >30 minutes
- Users cancel during indexing
- High CPU usage with no progress indication
- Tool appears frozen

**Phase impact:** Must be optimized in Phase 2 (embedding). Poor first-run experience kills adoption.

**Sources:**
- [Introducing EmbeddingGemma](https://developers.googleblog.com/introducing-embeddinggemma/)
- [Best Open-Source Embedding Models Benchmarked](https://supermemory.ai/blog/best-open-source-embedding-models-benchmarked-and-ranked/)
- [Best Embedding Models 2025](https://artsmart.ai/blog/top-embedding-models-in-2025/)

---

### Pitfall 12: Overlooking Metadata for Query Performance
**What goes wrong:** Storing only embeddings without metadata (timestamp, sender, conversation ID) means you can't filter results, leading to irrelevant retrieval and poor performance.

**Prevention:**
- Store metadata alongside embeddings: timestamp, sender, chat_id, is_from_me
- Support filtering: "messages from Alice last month"
- Enable hybrid queries: semantic + metadata filters
- Index metadata fields for performance
- Provide rich filtering in retrieval

**Detection:**
- Cannot filter by date range or sender
- Irrelevant results from wrong conversations
- Must scan entire vector DB for simple queries

**Phase impact:** Must be designed in Phase 2 (vector DB schema). Hard to retrofit.

**Sources:**
- [Common Pitfalls Using Vector Databases](https://dagshub.com/blog/common-pitfalls-to-avoid-when-using-vector-databases/)

---

### Pitfall 13: Incorrect Vector Dimensionality Trade-offs
**What goes wrong:** Using high-dimension embeddings (e.g., 1536D) consumes excessive memory and storage for 100K+ messages without proportional accuracy gains. Costs spiral unnecessarily.

**Prevention:**
- Test smaller embedding models (384D or 768D)
- Implement quantization: reduce 32-bit floats to 8-bit integers (75% memory reduction)
- Benchmark accuracy vs memory trade-offs
- Choose dimension based on actual accuracy needs, not "bigger is better"
- Document memory requirements clearly

**Detection:**
- High memory usage (>4GB for 100K messages)
- Slow vector search despite small dataset
- Storage size grows unexpectedly

**Phase impact:** Decided in Phase 2 (embedding model selection). Affects scalability.

**Sources:**
- [Common Pitfalls Using Vector Databases](https://dagshub.com/blog/common-pitfalls-to-avoid-when-using-vector-databases/)
- [Vector Embeddings - OpenAI](https://platform.openai.com/docs/guides/embeddings)

---

## Minor Pitfalls

### Pitfall 14: Tapbacks and Reactions Parsing
**What goes wrong:** Tapbacks (reactions) are stored differently than regular messages. They reference the original message GUID and have special formatting. Ignoring them loses conversational context.

**Prevention:**
- Parse `associated_message_guid` to link reactions to original messages
- Handle emoji Tapbacks (iOS 18+) vs standard 6 reactions
- Decide whether to index reactions separately or merge with original message
- Account for cross-platform reaction rendering (iOS 16+ improved Android compatibility)

**Detection:**
- Reactions appear as separate confusing messages
- "Loved 'message text'" shows up instead of inline reaction
- Search doesn't account for reactions indicating importance

**Phase impact:** Addressed in Phase 1 (parsing). Nice-to-have, not critical.

**Sources:**
- [How to See All People Who Tapbacked on iMessage](https://ios.gadgethacks.com/how-to/see-all-people-who-tapbacked-imessage-0384700/)
- [iOS 16 Fixes Annoying Message Reactions](https://www.digitaltrends.com/phones/ios-16-message-reactions-tapback-spam-android/)

---

### Pitfall 15: Message Threads Parsing (iOS 14+)
**What goes wrong:** Threaded replies (introduced iOS 14) use `thread_originator_guid` to reference parent messages. Ignoring threads loses conversational structure.

**Prevention:**
- Parse thread relationships from `thread_originator_guid`
- Build conversation trees, not flat lists
- Provide context from parent message when displaying reply
- Handle cases where thread parent is outside retrieved context

**Detection:**
- Thread replies appear out of context
- Users confused by responses that don't make sense without parent
- Search results show replies but not original question

**Phase impact:** Addressed in Phase 1 (parsing). Improves context quality.

**Sources:**
- [iOS 14 Message Mentions and Threading](https://blog.d204n6.com/2020/09/ios-14-message-mentions-and-threading.html)

---

### Pitfall 16: Privacy - Accidental Logging of Sensitive Messages
**What goes wrong:** Verbose logging during development captures message content in log files, which get committed to git or persist in production, leaking private conversations.

**Prevention:**
- Never log message content, only IDs/counts
- Sanitize logs before committing
- Use debug mode that's OFF by default
- Store logs locally only, never remote
- Implement log rotation and automatic cleanup
- Use PiiCatcher or similar tools to scan for accidental PII in logs

**Detection:**
- grep logs for phone numbers, names, message patterns
- Code review catches log statements with message variables
- Automated PII detection in CI

**Phase impact:** Ongoing concern across all phases. Requires discipline.

**Sources:**
- [How I Detected Log Leaks in Open Source Projects](https://www.piiano.com/blog/application-data-leaks)
- [Top Open Source Sensitive Data Discovery Tools](https://www.bytebase.com/blog/top-open-source-sensitive-data-discovery-tools/)
- [8 Tools to Protect Sensitive Data from Unintended Leakage](https://odsc.medium.com/8-tools-to-protect-sensitive-data-from-unintended-leakage-7d20dc0d44ad)

---

### Pitfall 17: ANSI Formatting Leakage in CLI Output
**What goes wrong:** Forgetting to send ANSI reset after styled messages causes all subsequent terminal output to inherit the formatting, making the terminal unreadable.

**Prevention:**
- Always send ANSI reset (`\033[0m`) after colored/styled output
- Use libraries like `rich` or `colorama` that handle this automatically
- Test output in multiple terminals (Terminal.app, iTerm2, VS Code)
- Provide `--no-color` flag for environments that don't support ANSI

**Detection:**
- Terminal output has wrong colors after tool exits
- Prompt inherits tool's formatting
- User complaints about "broken terminal"

**Phase impact:** Addressed in Phase 3 (CLI UX). Easy fix if caught early.

**Sources:**
- [Chat REPL Guide](https://github.com/sigoden/aichat/wiki/Chat-REPL-Guide)
- [Replit CLUI: Building a Graphical Command Line](https://blog.replit.com/clui)

---

### Pitfall 18: Streaming Response Buffering Issues
**What goes wrong:** LLM streaming responses arrive in chunks but get buffered, appearing jerky or in large batches instead of smooth token-by-token display.

**Prevention:**
- Use `httpx` with `httpx-sse` for proper SSE streaming
- Set `--no-buffer` when using curl for testing
- Flush stdout after each token: `sys.stdout.flush()`
- Handle `\r\n\r\n` delimiters correctly for SSE
- Test that responses appear incrementally, not in bursts

**Detection:**
- Text appears in chunks every 1-2 seconds instead of smoothly
- Terminal shows nothing then dumps entire response at once
- Users perceive tool as slow despite streaming enabled

**Phase impact:** Addressed in Phase 3 (LLM streaming). UX issue, not functional.

**Sources:**
- [How LLMs Stream Responses](https://developer.chrome.com/docs/ai/streaming)
- [Streaming LLM Responses - Tutorial](https://medium.com/@zh2408/streaming-llm-responses-tutorial-for-dummies-using-pocketflow-417ad920c102)
- [Best Practices to Render Streamed LLM Responses](https://developer.chrome.com/docs/ai/render-llm-responses)

---

### Pitfall 19: Ctrl-C Interrupt Handling
**What goes wrong:** Not handling SIGINT (Ctrl-C) gracefully leaves partial state, corrupted indexes, or orphaned processes. Users forced to kill -9.

**Prevention:**
- Catch KeyboardInterrupt exception for graceful shutdown
- Register signal handler for SIGINT: `signal.signal(signal.SIGINT, handler)`
- Clean up resources (close DB connections, flush indexes) on interrupt
- Show "Interrupting..." message so user knows it's handling
- For asyncio, use proper signal handling for async contexts
- Note: only main thread receives signals, not worker threads

**Detection:**
- Ctrl-C leaves tool running in background
- Database locked after interrupt
- Partial index updates cause corruption

**Phase impact:** Addressed in Phase 3 (CLI robustness). Important for good UX.

**Sources:**
- [Handling and Confirming Signals in Python](https://davidhamann.de/2022/09/29/handling-signals-in-python/)
- [Capturing and Handling OS Signals in Python](https://www.xanthium.in/operating-system-signal-handling-in-python3)
- [Asyncio Handle Control-C](https://superfastpython.com/asyncio-control-c-sigint/)

---

### Pitfall 20: macOS Epoch Time Conversion
**What goes wrong:** Timestamps in chat.db use macOS epoch (2001-01-01) instead of Unix epoch (1970-01-01). Failing to convert shows messages from 1970 or wrong dates entirely.

**Prevention:**
- Convert timestamps: `unix_timestamp = macos_timestamp + 978307200`
- Helper function:
  ```python
  from datetime import datetime, timedelta

  def macos_to_datetime(macos_timestamp):
      mac_epoch = datetime(2001, 1, 1)
      return mac_epoch + timedelta(seconds=macos_timestamp)
  ```
- Apply to all date fields: `date`, `date_read`, `date_delivered`

**Detection:**
- Messages show dates in 1970 or way off
- Chronological ordering is wrong
- Recent messages appear as very old

**Phase impact:** Addressed in Phase 1 (parsing). Simple fix, easy to catch.

**Sources:**
- [Analyzing iMessage Conversations](https://stmorse.github.io/journal/iMessage.html)
- [Searching iMessage Database with SQL](https://spin.atomicobject.com/search-imessage-sql/)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1: chat.db Access | AttributedBody, Full Disk Access, WAL journal mode | Test on Ventura+, handle permissions gracefully, copy DB before reading |
| Phase 2: RAG Implementation | Fixed-size chunking, embedding model selection | Use semantic chunking, choose stable model, plan for re-indexing |
| Phase 2: Vector DB | Metadata design, dimensionality | Design schema upfront, benchmark small vs large models |
| Phase 3: LLM Integration | Context window degradation, streaming buffering | Implement reranking, use SSE properly |
| Phase 3: CLI UX | ANSI formatting, Ctrl-C handling, progress indication | Use `rich` library, handle signals, show progress for long operations |
| Phase 5: Distribution | Homebrew sdist requirements, PEP 668 compliance | Verify all deps have sdist, use clean venv for formula generation |

---

## Research Confidence Assessment

| Area | Confidence | Source Quality |
|------|------------|----------------|
| chat.db parsing | HIGH | Official documentation, GitHub implementations, community forums |
| RAG chunking | HIGH | 2025 research papers, established best practices, production examples |
| Vector embeddings | HIGH | Official vendor docs, benchmarks, technical blogs |
| CLI/REPL design | MEDIUM | Community practices, tool documentation, limited official guidance |
| Homebrew packaging | HIGH | Official Homebrew docs, maintainer guidelines |
| macOS permissions | HIGH | Official Apple documentation, recent 2025 sources |
| Privacy/security | MEDIUM | DLP tool documentation, security blogs, general best practices |

---

## Additional Research Needed

These topics may require deeper investigation in specific phases:

1. **Attachment handling**: How to index images, audio messages, files sent in iMessage
2. **Incremental indexing strategy**: Efficiently detecting and indexing new messages without full re-scan
3. **Cross-device message sync**: Handling messages that exist on iPhone but not Mac, or vice versa
4. **iMessage vs SMS differentiation**: Whether to treat them differently for RAG purposes
5. **Conversation boundary detection**: Algorithm for determining when one conversation ends and another begins based on time gaps
6. **Hybrid search implementation**: Specific approach for combining BM25 + vector search for iMessage queries
7. **Multi-user support**: If tool should support multiple macOS users on same machine
8. **Data retention policies**: Whether to respect Messages app's auto-delete settings
