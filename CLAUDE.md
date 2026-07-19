# THE NEGOTIATOR — project context for Claude Code

This repo is our completed submission to the ElevenLabs "Negotiator" challenge
at Hack-Nation #6 (July 2026), now maintained as a portfolio artifact. The
frozen evidence in `benchmark/golden_calls/` is the point of the repo — treat
it as read-only. The sections below were the working context during the
hackathon and remain accurate as project documentation.

## Mission & thesis
Voice agent that calls moving companies, extracts itemised quotes, and negotiates.
The brief's decisive judging line: *"at least one negotiation shows the price
measurably change during the call because of leverage the agent gathered."*
Most teams will script this. **We measure it.** Our differentiator is
`benchmark/harness.py`: it computes total price movement, the portion
attributable to leverage events, and an honesty scorecard from `price_events`
evidence in each call. The pitch opens with that number. Protect this asset —
everything else serves it.

## Locked decisions — do not relitigate
- **Vertical:** moving (brief supplies pain data + benchmarks; zero data-sourcing time)
- **Counterparties:** 3 ElevenLabs counter-agents (aggressive / evasive / honest
  personas in `prompts/counter_agents/`) reached over **real Twilio telephony** —
  this satisfies "live calls against 3 distinct negotiation styles"
- **Stack:** Python FastAPI + ElevenLabs Agents Platform + Twilio + Streamlit;
  **file-based JSON storage** (no DB — keep it that way, one person must run everything)

## Repo map
- `schema/job_spec.schema.json` — single confirmed job spec, reused verbatim on every call
- `schema/quote.schema.json` — per-call quote; `price_events[]` (timestamped price +
  trigger + transcript snippet) is what makes negotiation measurable. Never weaken it.
- `prompts/` — system prompts: Estimator (intake), Caller/Closer (negotiation), 3 personas
- `server/main.py` — FastAPI: spec storage, call kickoff, mid-call quote webhook, transcripts
- `server/elevenlabs_client.py` — outbound-call client. **Verify the endpoint against
  current ElevenLabs Agents Platform docs before first use** (flagged in code)
- `server/quote_extractor.py` — transcript → quote JSON via Claude (batch step)
- `server/redflag.py` — lowball/above-market/conditional-fee flags (seed benchmarks — replace with moveBuddha/FMCSA numbers and cite)
- `benchmark/harness.py` — THE differentiator (smoke-tested, working)
- `report/app.py` — Streamlit ranked report; ranks on price AND terms, penalises red flags
- `benchmark/golden_calls/` — frozen best recordings + quotes; regression set after prompt tweaks

## Final state (post-hackathon)
Pipeline ran end to end via the ElevenLabs simulation API (real telephony was
built but blocked by a Twilio account-level compliance requirement — see README
"Limitations"). Measured result: £410 movement across 3 personas, 100%
leverage-attributed, best call £2,100→£1,740 (17.1%). Frozen in
benchmark/golden_calls/ with the harness output.

## Roles
See **WORKSTREAMS.md** — file-level ownership, no overlap, schemas are the contract.
Matthew = Workstream A (pipeline: calls, intake, report). Shehab = Workstream B
(evaluation: personas, harness, extraction QA). Never edit the other workstream's
files — log the request in HANDOFFS.md instead. Work Claude Code does should
default to unblocking the critical path first.

## Critical path — in order, riskiest first
1. **One real outbound call**: provision ElevenLabs Caller agent + one counter-agent,
   import Twilio number, place a call, capture transcript. Everything else is easy
   once this works. *Fallback if telephony fights us:* ElevenLabs agent-to-agent
   in-platform, disclosed honestly in the demo.
2. Estimator voice intake → one confirmed `job_spec` stored via `/jobspec`.
3. Clone to 3 personas; run calls; `quote_extractor` → report fills with real data.
4. Harness over the real calls → record the golden call where price visibly drops
   on a leverage line → pitch built around the measured number.
5. Stretch only if time remains: doc/photo intake, richer report, red-flag benchmarks
   from real moveBuddha data.

## Non-negotiables (from the judging brief — breaking any of these loses)
- The confirmed job spec is described **identically** on every call.
- If asked whether it's an AI, the agent **says yes immediately** and continues.
- The agent **never invents** competing bids, inventory, or constraints.
  `server/main.py` enforces this structurally (only real stored binding quotes are
  injected as `{{best_quote}}`) — do not remove that guarantee.
- Every call ends structured: itemised quote / committed callback / documented decline.
- Quotes 30%+ below market are flagged as lowballs, not chased.
- Demo checklist in README.md maps 1:1 to the rubric — keep it current.

## Working style
- No over-engineering: no new services, no DB, no auth, minimal new dependencies.
- Small, frequent commits; keep the app runnable at every commit.
- After any prompt change, re-run `python -m benchmark.harness` over golden calls.
- When an external API shape is uncertain (ElevenLabs, Twilio), check current docs
  rather than guessing.
