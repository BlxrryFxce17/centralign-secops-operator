# CentrAlign AI — Google Form Submission Answers

Here are your exact, copy-paste ready answers. I rewrote them to sound much more natural, direct, and conversational—exactly like a real engineer explaining their project.

---

### Q1. In 3–5 sentences, what did you build?
I built an autonomous SecOps operator that handles enterprise identity and security tasks, like offboarding employees or revoking access keys. Instead of just answering prompts, the agent reads internal security policies, breaks down the goal into steps, and executes them against simulated tools (like Okta, AWS IAM, and MDM). It has a built-in approval flow that pauses dangerous actions (like locking out a CISO) so a human can approve them first. Finally, it uses an independent checker to query the database directly and verify the job actually got done, rather than just trusting the LLM's word for it.

### Q2. Briefly explain your architecture
The core is a custom Python (FastAPI) execution engine that runs an 8-step loop: understand, plan, execute, observe, adapt, verify, and complete. I didn't use Langchain or CrewAI; I built the reasoning loop from scratch so I could easily plug in OpenAI, Gemini, or Claude. The frontend is a vanilla JS dashboard that streams real-time WebSockets so you can watch exactly what the agent is thinking and doing. For the enterprise environment, I used a real SQLite database to simulate the APIs, which forced the agent to deal with actual relational data, strict state changes, and audit logs instead of just easy mocked responses.

### Q3. What parts of your system are genuinely autonomous?
The agent is completely autonomous when it comes to planning steps, picking which tools to use, and recovering from errors. For example, if it hits a rate limit error from a simulated API, it automatically backs off and retries on its own. It also handles mapping casual names (like "Vikram") to actual database IDs by autonomously searching its JSON memory store. The only time it stops on purpose is when it hits a high-risk action that requires a human manager to click "approve" before it continues.

### Q4. What is currently hard coded or manually configured?
The company security policies and the approval rules are manually configured in a static `security_sop.json` file. Because I wanted to keep the project safe and sandboxed, the external APIs (like AWS or Jamf) are hard-coded to route to my local Python functions that update the SQLite database. Also, the final verification step uses hard-coded SQL queries to check the database state, which ensures the verification is completely independent from the LLM.

### Q5. What models, frameworks, APIs, libraries, AI coding tools, or existing projects did you use?
**Backend**: Python 3.12, FastAPI, Uvicorn, and WebSockets for real-time streaming.
**Data**: Pydantic v2 for validation and SQLite for the simulated environment.
**Frontend**: Just pure HTML, CSS, and Vanilla JS.
**CLI**: The Python `rich` library for the terminal UI.
**AI / Models**: The orchestration is entirely custom-built from scratch (no Langchain or CrewAI). I built the LLM provider to be model-agnostic, and I mainly tested it with Gemini 1.5 Pro and GPT-4o.
**Testing**: Pytest.

### Q6. What is the biggest technical limitation of your current solution?
Right now, the execution engine just runs in a single Python process and stores active tasks in memory. If the server restarts while a task is paused waiting for a human to approve it, that specific task's context is lost and can't be resumed from the database yet. Also, the agent runs tools one by one sequentially, so it can't fire off multiple network requests at the exact same time to gather data faster.

### Q7. If you had another 2 weeks, what would you build/change next?
1. **Durable Orchestration**: I'd migrate the core loop to something like Temporal.io so the state machine can survive server crashes and restarts without losing track of active tasks.
2. **Real Browser Sandbox**: I'd replace the simulated web tools with a real containerized Playwright setup so the agent could actually navigate legacy web portals that don't have APIs.
3. **Multi-Agent Setup**: I'd split the monolithic operator into smaller, specialized agents (like an Auditor agent and an IAM agent) that communicate with each other.
4. **Learning from Feedback**: I'd add a feature where if a human rejects an action during the approval phase, the agent permanently remembers the correction for next time.
