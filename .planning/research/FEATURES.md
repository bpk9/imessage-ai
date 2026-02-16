# Feature Landscape

**Domain:** AI-powered personal chat history analysis (CLI)
**Researched:** 2026-02-16

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Semantic Search** | Standard in modern AI chat tools. Users expect natural language queries, not keyword matching | Medium | Requires vector embeddings (ChromaDB/similar), OpenAI or local embeddings. MiMessage demonstrates this is expected for iMessage tools |
| **Natural Language Query Interface** | AI chat tools use conversational interface, not SQL-like syntax | Low | Users type questions like "what did sarah say about the party?" |
| **Privacy-First Local Processing** | Personal message data is highly sensitive. Cloud-only = instant rejection | Medium | Local LLM support (Ollama) is table stakes. Cloud opt-in is acceptable, cloud-required is not |
| **Message Context/History** | Conversations are multi-turn. Tool must maintain context across questions | Medium | Store conversation history, send relevant context with each query. Sliding window or summarization required |
| **Basic Message Stats** | Users expect counts, date ranges, frequency metrics | Low | Message count by person, date range, messages/day. Basic SQL queries |
| **Data Export** | Users want to own their data and back it up | Low | Export to JSON, CSV, Markdown. Standard feature in all chat tools surveyed |
| **Conversation Filtering** | Search within specific contacts, date ranges, or groups | Low | Filter by contact, date range, group chat. Essential for large message DBs |
| **Fast Response Time** | Interactive chat requires sub-second query responses | High | Vector DB must deliver sub-100ms retrieval. Critical for REPL experience |
| **Multi-line Input** | Complex queries need multi-line composition | Low | Standard REPL feature. See aichat, Claude Code CLI |
| **Command History** | Users expect up-arrow to recall previous queries | Low | Standard terminal behavior. All modern CLI tools have this |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Insight Commands** | Proactive analytics vs reactive search. "Tell me something I don't know" | High | Relationship analytics, communication patterns, self-reflection prompts. MosaicChats shows market demand |
| **Relationship Analytics** | Understand communication dynamics, compatibility, emotional trends | High | Sentiment timelines, response time patterns, conversation balance, topic clustering. ChatRecap AI shows this is valued |
| **Terminal Visualization** | Rich data insights without leaving terminal | Medium | ASCII charts for trends, sparklines for message frequency, word clouds. Differentiates from web-only tools |
| **Self-Improvement Suggestions** | AI suggests how to improve communication based on patterns | High | Analyzes tone, response times, conversation balance. Personal analytics trend (MindScape research) |
| **Topic Mapping** | Automatic discovery of conversation themes over time | Medium | LLM-powered topic extraction, visualization of topic evolution. Helps rediscover forgotten conversations |
| **Interactive REPL with Autocomplete** | Professional CLI experience, not basic prompt | Medium | Tab completion for commands, slash commands, vim keybindings. Modern CLI standard (aichat, Claude Code) |
| **Conversation Summarization** | Quick overview of long conversation threads | Medium | LLM generates summaries of date ranges or specific contacts. Rewind.ai shows this is highly valued |
| **Local-First with Cloud Opt-in** | Privacy + power user flexibility | Medium | Default to Ollama, allow OpenAI/Claude for better results. Balance privacy and quality |
| **Hybrid Search** | Semantic + keyword for acronyms, names, specific phrases | Medium | Combine vector search with SQLite FTS. Best practice for RAG 2026 |
| **Chat Sessions** | Persistent conversations, save/load analysis sessions | Low | Name and resume analysis sessions. Enables iterative exploration |
| **Sentiment Analysis Over Time** | Emotional arc of relationships visualized | Medium | Track sentiment trends, identify relationship inflection points. ChatRecap AI feature |
| **Group Chat Dynamics** | Who dominates conversations, response patterns, subgroups | High | Analyze group participation, identify cliques, conversation starters. Unique to group messaging |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Web UI** | Scope creep, maintenance burden, not differentiating | Stay CLI-only. Terminal visualizations are enough |
| **Real-time Message Monitoring** | Privacy concerns, complexity, battery drain | Batch mode only. Analyze existing DB, don't monitor live |
| **Cloud Storage of Messages** | Privacy violation, liability, against core value prop | Local-only storage. Never upload message content to servers |
| **Message Sending** | Out of scope, security risk, not analysis tool | Read-only. Use Messages app for sending |
| **Custom Embeddings Training** | Overkill, slow, not needed for personal scale | Use OpenAI/Ollama embeddings. Don't train custom models |
| **Multi-platform Support** | iMessage is macOS-only. Android/Windows pointless | macOS-only. chat.db is macOS-specific |
| **GUI Configuration** | CLI tool, config file is sufficient | YAML/JSON config file. Keep it terminal-native |
| **Automated Posting/Sharing** | Privacy risk, not core use case | Manual export only. User controls what leaves the tool |
| **Contact Syncing** | Already in chat.db, no need to integrate other sources | Use existing contact data in Messages DB |

## Feature Dependencies

```
Semantic Search → Vector Database (ChromaDB/similar)
Semantic Search → Embeddings (OpenAI or Ollama)
Natural Language Query → LLM (OpenAI/Claude/Ollama)
Insight Commands → LLM + Vector Search + Stats
Relationship Analytics → Sentiment Analysis + Time Series Analysis
Topic Mapping → LLM + Clustering
Terminal Visualization → ASCII charting library
Hybrid Search → Vector DB + SQLite FTS
Conversation Summarization → LLM + Context Window Management
Self-Improvement Suggestions → Sentiment Analysis + Communication Patterns
Group Chat Dynamics → Graph Analysis + Clustering
```

## MVP Recommendation

Prioritize (Phase 1 - Core Search):
1. **Semantic Search** - Core value prop, table stakes
2. **Natural Language Query Interface** - Essential for AI tool
3. **Privacy-First Local Processing** - Core differentiator
4. **Message Context/History** - Required for multi-turn chat
5. **Basic REPL** - Multi-line input, history, basic UX
6. **Conversation Filtering** - Essential for usability

Prioritize (Phase 2 - Insights):
1. **Insight Commands** - Primary differentiator
2. **Basic Message Stats** - Foundation for analytics
3. **Relationship Analytics** - High-value insights
4. **Terminal Visualization** - Makes insights accessible

Defer to Post-MVP:
- **Topic Mapping** - Complex, requires good LLM, can add later
- **Self-Improvement Suggestions** - Nice-to-have, not essential
- **Group Chat Dynamics** - Niche use case, advanced feature
- **Conversation Summarization** - Useful but not critical for launch
- **Chat Sessions** - Quality of life, not core functionality
- **Hybrid Search** - Optimization, semantic search alone is MVP
- **Sentiment Analysis Over Time** - Part of relationship analytics, iterative

Never Build:
- All anti-features listed above

## Feature Complexity Assessment

### Low Complexity (< 1 day)
- Basic Message Stats
- Data Export
- Conversation Filtering
- Multi-line Input
- Command History
- Chat Sessions

### Medium Complexity (1-3 days)
- Semantic Search (using existing libraries)
- Message Context/History
- Privacy-First Local Processing (Ollama integration)
- Terminal Visualization
- Interactive REPL with Autocomplete
- Conversation Summarization
- Hybrid Search
- Sentiment Analysis Over Time
- Local-First with Cloud Opt-in
- Topic Mapping

### High Complexity (3-7 days)
- Fast Response Time (optimization, indexing strategy)
- Insight Commands (requires orchestration of multiple analyses)
- Relationship Analytics (complex metrics, multiple dimensions)
- Self-Improvement Suggestions (requires sophisticated LLM prompting)
- Group Chat Dynamics (graph analysis, clustering algorithms)

## Sources

**AI-Powered Personal Data Tools:**
- [Rewind AI Features](https://www.rewind.ai/)
- [Rewind AI Review 2026](https://aichief.com/ai-productivity-tools/rewind-ai/)
- [Mem AI Knowledge-Aware Assistant](https://newsletter.mem.ai/p/introducing-the-worlds-first-knowledge)
- [Mem 2.0 AI Thought Partner](https://get.mem.ai/blog/introducing-mem-2-0)

**iMessage-Specific Tools:**
- [MiMessage - Semantic Search for iMessage](https://blog.jonlu.ca/posts/mimessage)
- [ChatRecap AI - iMessage Analysis](https://apps.apple.com/us/app/chatrecap-ai-chat-analysis/id6738325645)
- [iMessageAnalyzer GitHub](https://github.com/dsouzarc/iMessageAnalyzer)
- [iMessage Analytics macOS App](https://github.com/seanrayment/imessage-analytics)

**Chat Analysis & Relationship Insights:**
- [MosaicChats - Relationship Analytics](https://www.mosaicchats.com/chat-analysis)
- [Complete Guide to Chat Analysis 2025](https://www.mosaicchats.com/blog/complete-guide-chat-analysis-2025)
- [Personal Analytics & Self-Reflection](https://medium.com/@ann_p/from-quantified-self-to-qualitative-self-ai-shifting-focus-in-personal-analytics-68209a851322)

**RAG & Vector Search Best Practices:**
- [RAG Best Practices 2026](https://www.techment.com/blogs/rag-in-2026/)
- [Vector Databases for RAG Applications](https://azumo.com/artificial-intelligence/ai-insights/top-vector-database-solutions)
- [Complete Guide to RAG and Vector Databases](https://solvedbycode.ai/blog/complete-guide-rag-vector-databases-2026)

**CLI Interface Design:**
- [AIChat - LLM CLI Tool](https://github.com/sigoden/aichat)
- [Chat REPL Guide](https://github.com/sigoden/aichat/wiki/Chat-REPL-Guide)
- [Command Line Interface Guidelines](https://clig.dev/)
- [Modern CLI Tools 2026](https://medium.com/the-software-journal/7-modern-cli-tools-you-must-try-in-2026-c4ecab6a9928)

**Local AI & Privacy:**
- [Ollama Local AI Guide 2026](https://lalatenduswain.medium.com/the-ultimate-guide-to-running-open-source-ai-models-locally-with-ollama-in-2026-f9867a4a9cbe)
- [Local LLMs Privacy Guide](https://www.sitepoint.com/definitive-guide-local-llms-2026-privacy-tools-hardware/)
- [Privacy-First AI Tools](https://www.privacyguides.org/en/ai-chat/)

**Context Management:**
- [AI Chat Memory Implementation](https://getstream.io/blog/ai-chat-memory/)
- [Chat History Management GitHub](https://github.com/wyne1/chatbot-history-management)
- [Context-Aware Chatbot Development](https://dialzara.com/blog/context-aware-chatbot-development-guide-2024)

**Terminal Visualization:**
- [ASCII Chart CLI](https://github.com/kroitor/asciichart)
- [CLI Charting Tools](https://www.baeldung.com/linux/cli-charting-and-plotting-tools)
- [Terminal Data Visualization](https://medium.com/@SrvZ/how-to-create-stunning-graphs-in-the-terminal-with-python-2adf9d012131)
