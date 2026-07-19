# THE NEGOTIATOR — project context for Claude Code

A voice-AI negotiation system with a measurement harness, maintained as a
personal portfolio project. The frozen evidence in `benchmark/golden_calls/`
is the point of the repo — treat it as read-only.

## What it is
A voice agent that calls moving companies, extracts itemised quotes, and
negotiates. The differentiator is `benchmark/harness.py`: it computes total
price movement, the portion attributable to leverage events, and an honesty
scorecard from `price_events` evidence in each call. Everything else serves
that measurement. Protect it.

## Locked architecture decisions
- **Vertical:** moving.
- **Counterparties:** 3 persona counter-agents (aggressive / evasive / honest,
  in `prompts/counter_agents/`) with sharp, distinct concession rules — run
  agent-vs-agent via the ElevenLabs simulation API. Real Twilio telephony is
  built (`server/elevenlabs_client.py`, provisioning in `scripts/`) but
  blocked by a Twilio account-compliance rule (Business Trust Hub profile
  required for +1 calls from non-US accounts; error 21216).
- **Stack:** Python FastAPI + ElevenLabs Agents Platform + Streamlit;
  **file-based JSON storage** (no DB — keep it that way; one person must be
  able to run everything).
- **Schemas are the contract** (`schema/*.json`): call-producing code and
  measurement code interact only through them. A silent schema change breaks
  the other side; never worth it.

## Repo map
- `schema/job_spec.schema.json` — single confirmed job spec, reused verbatim on every call
- `schema/quote.schema.json` — per-call quote; `price_events[]` (timestamped price +
  trigger + transcript snippet) is what makes negotiation measurable. Never weaken it.
- `prompts/` — system prompts: Estimator (intake), Caller/Closer (negotiation), 3 personas
- `server/main.py` — FastAPI: spec storage, call kickoff, mid-call quote webhook, transcripts
- `server/elevenlabs_client.py` — ElevenLabs API client (agents, tools, phone numbers, calls)
- `server/quote_extractor.py` — transcript → quote JSON via gpt-4o; honesty flags are
  evidence-gated (verbatim snippet verified against the transcript)
- `server/redflag.py` — lowball/above-market/conditional-fee flags (seed benchmarks)
- `benchmark/harness.py` — THE differentiator; `benchmark/golden_calls/` — frozen
  evidence + regression set (agent IDs redacted; data is read-only)
- `scripts/` — provisioning, simulation, runbook, seed job spec
- `report/app.py` — Streamlit ranked report; ranks on price AND terms, penalises red flags

## Non-negotiables (design rules the agent must not break)
- The confirmed job spec is described **identically** on every call.
- If asked whether it's an AI, the agent **says yes immediately** and continues.
- The agent **never invents** competing bids, inventory, or constraints.
  `server/main.py` enforces this structurally (only real stored binding quotes
  are injected as `{{best_quote}}`) — do not remove that guarantee.
- Every call ends structured: itemised quote / committed callback / documented decline.
- Quotes 30%+ below market are flagged as lowballs, not chased.

## Working rules
- No over-engineering: no new services, no DB, no auth, minimal new dependencies.
- Small commits; keep the app runnable at every commit.
- After any prompt change, re-run `python -m benchmark.harness` over golden calls.
- When an external API shape is uncertain (ElevenLabs, Twilio), check current
  docs rather than guessing.

## Final state
Measured result: £410 movement across 3 personas, 100% leverage-attributed,
best call £2,100→£1,740 (17.1%), honesty scorecard all green. Frozen in
`benchmark/golden_calls/` with the harness output. Known issues:
KNOWN_ISSUES.md.
