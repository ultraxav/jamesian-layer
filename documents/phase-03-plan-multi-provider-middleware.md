## Goal

Implement Phase 3 of [hackathon_spec.md](hackathon_spec.md) (§6 step 3): multi-provider middleware connecting the validated Tier 2 local runtime to Meta Llama models — abstract client, four provider clients, unified router, Llama Stack hook, and FastAPI middleware — with integration tests proving the contract without live credentials.

## Success Criteria

- `jamesian_layer.middleware.base_provider.BaseProviderClient` exposes the exact §5.6 ABC (`chat_completion`, `stream_chat`); all four provider clients implement it with no silent fallbacks on auth or HTTP errors.
- `MultiProviderClient` routes `meta | baseten | modal | fireworks` from `Settings`, rejects unknown providers with `ValueError`, and streams tool-call deltas identically across providers.
- `LlamaStackInteroceptiveHook` wires the real Phase 1 daemon, Phase 2 comparator/breaker/habit: `pre_tool_call` captures the efference copy and enforces taboo with an explicit allow/block verdict; `post_tool_call` records afferent feedback, advances the daemon, and returns the suffix; `intercept_cycle` returns a cached CPG routine or `None`.
- `FastAPIInteroceptiveMiddleware` injects `X-Jamesian-Sigma` / `X-Jamesian-Tcoil` per §5.6.
- `.venv/bin/python -m pytest tests/ -v` is fully green, Phases 1–2 included, with the three new integration files passing the §7.2 gates (`test_multi_provider.py`, `test_llama_stack_hook.py`, `test_kv_cache_preservation.py`; `test_fastapi_middleware.py` rides along per the spec tree).
- No provider credentials required to pass; no audit CLI, dashboard, or sim work (Phases 4–6).

## Approach

One shared OpenAI-compatible transport in the base class (`httpx.AsyncClient`, POST + minimal SSE `data:`-line parser, no extra streaming dep): Meta, Baseten, and Fireworks all speak OpenAI-style chat completions per spec, so per-provider subclasses set only base URL, auth header, and default model from `Settings`. Modal is the exception — it drives remote workers through the modal SDK, so `ModalClient` wraps `modal.Function` lookup behind an injectable `_invoke` hook that tests stub. Shared policy: 30 s `httpx.Timeout` module constant (no `Settings` change), non-2xx responses raise `ProviderError` carrying status and body, missing keys raise at call time. New runtime deps (`httpx`, `fastapi`, `modal`) go in `pyproject.toml` dependencies with lower-bound pins mirrored in `requirements.txt`. Tests never touch the network: `httpx.MockTransport` fakes the three HTTP providers, the stubbed `_invoke` fakes Modal, and the hook tests use the real daemon/comparator/breaker/habit tracker.

## Steps

1. **Dependencies** — add `httpx>=0.27`, `fastapi>=0.110`, `modal>=0.60` to `pyproject.toml` + `requirements.txt`; reinstall the venv (`uv pip install -e ".[dev]"`, needs network).
2. **`middleware/base_provider.py` (+ `__init__.py`)** — `BaseProviderClient` ABC verbatim per §5.6; shared `_post_json()` / `_stream_sse()` helpers on an `OpenAICompatibleClient` subclass; `ProviderError`; timeout constant. All `from_settings` constructors accept `**kwargs` forwarded to the client (test-only `transport`/`invoke` injection).
3. **HTTP provider clients** — `meta_client.py` (Meta Model API + Bearer key, default `meta-llama/Llama-3.3-70B-Instruct`), `baseten_client.py` (OpenAI-compatible endpoint `https://inference.baseten.co/v1` + key, default `meta-models/muse-spark-open-1026`), `fireworks_client.py` (OpenAI-compatible base URL + key, default Fireworks Llama 3.3 70B); each maps `Settings` keys, parses `choices[0].message` + `tool_calls`, and assembles streamed deltas (including `tool_calls[].function.arguments` fragments).
4. **`middleware/modal_client.py`** — `ModalClient` implementing the ABC over `modal.Function` lookup of `run_agent_worker` (app `jamesian-layer`, `A10G`, timeout 300 per §5.6); injectable `_invoke(payload)` hook; missing token raises at call time.
5. **`middleware/multi_provider.py`** — `MultiProviderClient(provider, settings)` delegating both ABC methods, `ValueError` on unknown provider, `list_providers()` helper.
6. **`middleware/llama_stack_hook.py`** — `LlamaStackInteroceptiveHook(daemon, comparator, breaker, taboo, habit)` per §5.6: `pre_tool_call` records the efference copy (timestamped, intent vector from tool args) and returns `{"allowed": bool, "reason": str}` against the taboo list; `post_tool_call` builds `AfferentFeedback` (raises `KeyError` on an unpaired call with no pending efference copy), calls `daemon.step_once()` with the measured latency, returns `format_suffix(state)`; `intercept_cycle(state)` returns `habit.step(state)` routine dict or `None`.
7. **`middleware/fastapi_middleware.py`** — `FastAPIInteroceptiveMiddleware` verbatim per §5.6 (two telemetry headers).
8. **Integration tests** — `tests/integration/__init__.py` + `test_multi_provider.py` (routing per provider, auth headers, SSE delta assembly, unknown-provider `ValueError`, `ProviderError` mapping, all via `MockTransport`/stubbed `_invoke`); `test_llama_stack_hook.py` (pre/post round-trip advances daemon state, taboo blocks a banned tool with explicit verdict, `intercept_cycle` returns a routine on quiescent state and `None` on surprise); `test_fastapi_middleware.py` (headers present and correctly rounded on a stub ASGI app, driven via `httpx.ASGITransport` — Starlette's `TestClient` is deprecated); `test_kv_cache_preservation.py` (prefix SHA-256 identical before/after suffix injection through the stream path; suffix parses via `TELEMETRY_PATTERN`).
9. **Commit split** (standing instruction, in order): transports + router → provider clients → hook + middleware → integration tests. Docs untouched.

## Validation Plan

- `uv pip install -e ".[dev]"` (with `UV_CACHE_DIR=/tmp/uv-cache`) — expected: `httpx`, `fastapi`, `modal` install cleanly.
- `.venv/bin/python -m pytest tests/ -v` — expected: full suite green, Phases 1–2 unbroken.
- `.venv/bin/python -m pytest tests/integration/ -v` — expected: the four new files pass offline with zero credentials in the environment.
- Manual: single `stream_chat` call against `MockTransport` returning a 3-chunk tool-call delta — expected: one assembled `tool_calls` entry with complete arguments.

Highest-risk validation: the live provider handshake (real keys, real endpoints) cannot run here — no `META/BASETEN/MODAL/FIREWORKS` credentials exist in this environment. `MockTransport` proves the contract; the first live `agency-audit run` in Phase 4 is the deferred live check. Update 2026-10-28: Baseten live handshake verified — smoke `chat_completion` returned `meta-models/muse-spark-open-1026`, `finish_reason stop`, correct content. Remaining live checks: Meta, Modal, Fireworks.

## Risks / Open Questions

- **Modal SDK surface:** the plan follows the §5.6 decorator sketch; if the installed `modal>=0.60` API differs (`App` vs `Stub`, lookup signature), adapt `modal_client.py` to the real SDK and note the delta — the `_invoke` seam keeps tests unaffected.
- **SSE shape drift:** the minimal parser handles OpenAI-style `data: [DONE]` streams; a provider-specific event envelope falls back to per-subclass override, not base-class complexity.
- **No retries:** single timeout, no backoff — deliberate for Phase 3; retry policy belongs with the Phase 4 audit harness if flakiness appears.

Open questions: None — all Phase 3 facts resolve to spec §5.6, §6 step 3, §7.2, §8, and the committed Phase 1–2 code.

## Sources

- https://pypi.org/pypi/httpx/json
- https://www.python-httpx.org/advanced/transports/
- https://pypi.org/pypi/fastapi/json
- https://pypi.org/pypi/modal/json
