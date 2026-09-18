# Production-Readiness Roadmap Update: LLM‑Based Routing

## Goal Description
Replace the current keyword‑based intent detection and tool‑calling logic in the SupervisorAgent (and related agents) with a Groq LLM chat model. The LLM will classify the user query, decide which sub‑agent to invoke, and optionally call tools directly based on the model's function calling capability. This will make the system more flexible and improve understanding of natural language queries.

## User Review Required
> [!IMPORTANT]
> The proposed changes introduce a new external dependency (Groq API) and modify the core routing flow. Ensure you have a valid Groq API key and are comfortable with the added latency and cost.

## Open Questions
> [!WARNING]
> - Which Groq model should be used (e.g., `mixtral-8x7b-32768`)?
> - Do you want to keep a fallback to keyword routing for safety?
> - Should the LLM also perform tool/function calling for actions like fetching order status, or keep that logic in the existing tools?

## Proposed Changes
---
### Supervisor Agent
#### [MODIFY] [supervisor.py](file:///c:/Users/hp/ProdAI/OnlineFood/app/agents/supervisor.py)
- Remove keyword‑based intent detection blocks.
- Add a new method `classify_intent_via_llm(state: AgentState) -> dict` that:
  1. Retrieves `query` from state.
  2. Calls Groq chat completion with a system prompt describing possible intents (`ORDER_QUERY`, `MENU_QUERY`, `SUPPORT_QUERY`).
  3. Uses function calling schema to return `{ "intent": "...", "target_agent": "..." }`.
- In `route()`, replace existing logic with a call to `classify_intent_via_llm` and use its result to set `state["intent"]` and `state["next_agent"]`.
- Add error handling: if the LLM request fails, fall back to the existing keyword logic.

---
### Configuration
#### [MODIFY] [settings.py] (create if not present)
- Add `GROQ_API_KEY` loaded from environment variable.
- Add `GROQ_MODEL` default value (e.g., `mixtral-8x7b-32768`).

---
### Dependency Updates
#### [MODIFY] [requirements.txt]
- Add `groq>=0.2.0` (or latest version).

---
### Tool Integration (optional)
If you want the LLM to directly invoke existing tools (e.g., order lookup), define function schemas in the Groq request matching the signatures of `order_tools.py` and `menu_tools.py`. This can be added later as an incremental improvement.

---
### Caching & Rate Limiting
#### [MODIFY] [app/agents/utils.py] (create helper)
- Implement simple in‑memory cache (`functools.lru_cache` or `cachetools`) for recent queries to avoid repeated LLM calls.
- Add a rate‑limiter decorator using `asyncio.Semaphore` to respect Groq rate limits.

---
### Tests
#### [MODIFY] [test_suite.py]
- Add tests that mock the Groq client to verify routing decisions based on sample queries.
- Ensure existing tests still pass under the fallback path.

## Verification Plan
### Automated Tests
- Run the full test suite (`python -m pytest`).
- Add new unit tests for `SupervisorAgent.classify_intent_via_llm` with mocked responses.

### Manual Verification
- Start the FastAPI server locally and send sample queries for order, menu, and support. Verify the correct sub‑agent is invoked.
- Check logs for LLM call latency and fallback behavior.

---
