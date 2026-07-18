# THE NEGOTIATOR — Hack-Nation #6 (ElevenLabs challenge)

Voice agent that calls movers, gathers itemised quotes, and haggles — with a
**benchmark harness that proves the negotiation actually moved the price**.

Team: Matthew Huang · Shehab (AreedAdmin)

## Thesis
Most teams will script their "negotiation". We measure ours. The pitch leads with
one number: **£X saved / Y% price movement across N live calls — here's the harness.**

## Architecture

```
[Estimator]  ElevenLabs voice intake  ──►  job_spec.json (confirmed by user)
     │
[Caller]     ElevenLabs agent ── Twilio ──►  3 counter-agents (aggressive / evasive / honest)
     │                                        transcripts + price_events captured
[Closer]     cross-call leverage ("I have a binding quote for £1,850 — beat it?")
     │
[Report]     Streamlit ranked comparison + recommendation + evidence
[Harness]    benchmark/harness.py — savings, % movement, leverage attribution, honesty checks
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in keys
uvicorn server.main:app --reload --port 8000
streamlit run report/app.py
```

ElevenLabs side (dashboard):
1. Create the **Caller** agent from `prompts/caller_agent.md` (system prompt) — attach a
   `log_quote` client tool (webhook → `POST /calls/{call_id}/quote_event`).
2. Create 3 **counter-agents** from `prompts/counter_agents/*.md`, each bound to its own
   Twilio number (or test in-platform first, phone later).
3. Import your Twilio number under Phone Numbers, note `ELEVENLABS_PHONE_NUMBER_ID`.

## Demo checklist (maps 1:1 to the judging brief)
- [ ] Voice intake produces ONE confirmed job_spec, reused verbatim on every call
- [ ] Live calls vs 3 distinct negotiation styles, itemised comparable quotes
- [ ] ≥1 call where price measurably moves BECAUSE of leverage (harness proves it)
- [ ] AI discloses itself when asked; never invents inventory or fake bids
- [ ] Every call ends structured: itemised quote / callback / documented decline
- [ ] Ranked report cites transcripts + recordings, plain-language recommendation
- [ ] Close with the harness scoreboard number

## Build order (solo-friendly critical path)
1. Freeze `schema/job_spec.schema.json` (done — edit if needed)
2. One outbound call to ONE counter-agent, transcript captured  ← biggest risk, do first
3. Estimator intake → confirmed spec
4. 3 personas + quote extraction → report UI on real data
5. Harness numbers → record golden call → pitch
