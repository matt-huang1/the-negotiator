# WORKSTREAMS — who owns what

Two workstreams, one hard boundary: **the schemas are the contract.** Workstream A
produces calls and transcripts that conform to the schemas; Workstream B consumes
them and measures quality. As long as both sides respect `schema/*.json`, neither
ever blocks the other.

## Workstream A — Pipeline (Matthew)
**Mission: a real call happens end to end and its results are visible.**

Owns:
- `server/main.py`, `server/elevenlabs_client.py`
- `prompts/estimator_agent.md`, `prompts/caller_agent.md`
- `report/`
- `scripts/` (provisioning, tunnels)
- ElevenLabs + Twilio accounts, phone numbers, webhooks
- Demo recording + pitch

## Workstream B — Evaluation & Simulation (Shehab)
**Mission: the negotiation is real, distinct, and measurably proven.**

Owns:
- `prompts/counter_agents/` (persona concession rules stay sharp and distinct)
- `benchmark/` (harness, golden-call regression set)
- `server/quote_extractor.py`, `server/redflag.py` (extraction quality + flags)
- Demo video edit

## Shared — change only by quick agreement (message + thumbs-up)
- `schema/job_spec.schema.json`, `schema/quote.schema.json` — the contract.
  A silent schema change breaks the other workstream; never worth it.
- `README.md`, `CLAUDE.md`, `WORKSTREAMS.md`, `.env.example`, `requirements.txt`

## Working rules
1. Each of us runs our own Claude Code session and opens it with our workstream
   ("I'm working Workstream A/B — read CLAUDE.md and WORKSTREAMS.md").
2. Claude Code must NOT edit files owned by the other workstream. If a change is
   needed there, add an entry to `HANDOFFS.md` instead and carry on.
3. Commit prefix `[A]` or `[B]` so history shows who changed what. Push small and
   often to `main` — the ownership split is what prevents collisions, not branches.
4. After any prompt change (either side): `python -m benchmark.harness` over
   golden calls before pushing.
5. Blocked >30 min on your own side? Say so — the other picks it up and ownership
   of that item moves. The split serves the deadline, not the other way round.
