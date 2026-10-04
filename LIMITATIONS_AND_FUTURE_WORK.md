# CentrAlign AI — Known Limitations & Future Work

Honest engineering self-assessment of the current prototype and a prioritized technical roadmap for scaling to a production-grade enterprise employee.

---

## 1. Known Limitations of the Current Prototype

1. **Local Single-Node Runtime**:
   - The current engine runs in a single Python process using in-memory task tracking (`active_contexts`). If the host process restarts while a task is in `AWAITING_APPROVAL`, state must currently be re-hydrated from SQLite.
2. **Synchronous Tool Dispatching**:
   - Tools are currently executed sequentially. While this is optimal for linear workflows (e.g. search invoice $\to$ parse invoice $\to$ query PO $\to$ post), parallel independent actions (e.g. searching across 5 different document drives simultaneously) would benefit from concurrent worker dispatch.
3. **Simulated Browser Environment**:
   - The browser connector simulates DOM navigation and form submission without launching a full headless Chromium/Playwright instance. While sufficient for proof-of-concept validation, production environments require headless browser drivers capable of interacting with complex Single Page Apps (React/Angular) and handling CAPTCHAs.
4. **Vector Retrieval Scale**:
   - Company SOP retrieval uses keyword and structured JSON lookup. For organizations with thousands of pages of policy documents, a dense embedding vector store (e.g., Qdrant, pgvector) with hybrid BM25 search would provide higher recall.

---

## 2. What I Would Build Next (Future Roadmap)

If given additional time to evolve this prototype into a production-grade AI employee, here is what I would prioritize:

### Phase 1: Distributed Execution Engine (Temporal / Celery)
- **Durable Task Workflows**: Migrate `OperatorEngine` to a durable orchestration framework like **Temporal.io**. Every step, observation, and HITL suspension would be a durable event replayable across worker crashes.
- **Multi-Tenant State Store**: Back the execution context with PostgreSQL / Redis, allowing horizontal scaling across hundreds of worker nodes.

### Phase 2: Full Headless Computer-Use Sandbox (Playwright + Docker)
- **Isolated Browser Containers**: Spin up ephemeral Docker containers with headless Chromium and Playwright for real web scraping and UI automation.
- **Visual Grounding**: Integrate vision-language models (e.g., Claude 3.5 Sonnet Computer Use or Gemini 1.5 Pro) with coordinate-based mouse/keyboard interaction for legacy desktop applications that lack APIs.

### Phase 3: Dynamic Multi-Agent Collaboration
- **Specialized Employee Roles**: Instead of a monolithic operator, split the workload into specialized sub-agents:
  - *Auditor Agent*: Focuses exclusively on invariant checking and discrepancy detection.
  - *Navigator Agent*: Operates browsers and web portals.
  - *ERP Integrator Agent*: Manages API rate limits, schema validation, and SQL transactions.
- **Supervisor Coordinator**: Manages inter-agent message passing and consensus verification.

### Phase 4: Active Policy Learning & Feedback Loops
- **Reinforcement Learning from Human Feedback (RLHF)**: When a human manager rejects or modifies a proposed action during an HITL review, the system automatically captures the correction into persistent episodic memory, refining future planning prompts to prevent similar mistakes.
