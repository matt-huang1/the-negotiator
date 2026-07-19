# The Negotiator

A voice-AI agent that obtains — and then negotiates — itemised moving quotes.
The Caller agent describes a fixed, user-confirmed job spec to moving
companies, extracts an itemised quote, and negotiates using only real
leverage: an actual competing bid, genuine date flexibility, or bundling.
What separates it from a scripted demo is `benchmark/harness.py`, which
**measures** the negotiation instead of claiming it: total price movement, the
portion attributable to leverage events, and an honesty scorecard — all
computed from timestamped `price_events` evidence in each call. Built in 24 hours; preserved as a working artifact.

## Measured result

Frozen in [`benchmark/golden_calls/`](benchmark/golden_calls/) (transcripts,
extracted quotes, harness output):

```
Calls: 3  |  Distinct negotiation styles: 3
Total price movement:            £410
...attributable to leverage:     £410  (100%)
Best single call:                17.1%
Honesty — AI disclosure ok: True | invented bids: 0 | structured outcomes: 3/3
```

The best call, against the aggressive "anchor high, concede only under
pressure" persona: opening quote **£2,100** → **£1,890** when the agent cited
a real competing £1,550 binding quote → **£1,740** on weekday date
flexibility. The honest persona moved only £50 — correct behaviour, since it
was already fairly priced; the agent's job is to recommend on terms, not just
chase the lowest number.

Reproduce the scoreboard from the frozen evidence (no API keys needed):

```bash
mkdir -p data/quotes && cp benchmark/golden_calls/quote-*.json data/quotes/
python -m benchmark.harness
```

## Architecture

```
[Estimator]  ElevenLabs voice intake  ──►  job_spec.json (confirmed by user)
     │
[Caller]     ElevenLabs agent ──► counter-agent personas (aggressive / evasive / honest)
     │                            transcripts + price_events captured
[Extractor]  transcript ──► structured quote (gpt-4o, evidence-gated honesty flags)
     │
[Harness]    benchmark/harness.py — movement, leverage attribution, honesty checks
[Report]     Streamlit ranked comparison, penalises red flags
```

- **FastAPI server** (`server/`) — file-based JSON storage (no DB by design),
  call orchestration, mid-call `log_quote` webhook, transcript sync.
- **Honesty enforced structurally**: the only competing bid the Caller can
  cite is injected server-side from real stored binding quotes
  (`{{best_quote}}`); the extractor's invented-bid flag requires verbatim
  transcript evidence.
- **Schemas are the contract** (`schema/`): `job_spec` (described identically
  on every call) and `quote` with `price_events[]` — the measurement substrate.

## Run it yourself

See [`scripts/RUNBOOK.md`](scripts/RUNBOOK.md). Short version, with your own
ElevenLabs + OpenAI keys:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                        # fill the two keys + BASE_URL
python -m scripts.provision agents          # prints agent IDs → .env
mkdir -p data/specs && cp scripts/seed_jobspec.json data/specs/demo.json
python -m scripts.simulate_call --job demo --persona honest
python -m server.quote_extractor && python -m benchmark.harness
```

## Limitations

- **The counterparties are simulated — deliberately, and disclosed.**
  Measuring *leverage attribution* requires counterparties with known,
  controlled concession rules: each persona (aggressive / evasive / honest)
  has explicit rules about when it may concede, so a price drop after a
  leverage line is interpretable and every run is reproducible. Against real
  movers you get one uncontrolled sample per phone call. Real telephony was
  built end to end (Twilio number import, outbound-call endpoint, live
  webhook quote-logging — all verified) but is blocked on my account by a
  Twilio compliance rule: +1 calls from non-US accounts created after
  Oct 2025 require an approved Business Trust Hub profile (error 21216).
  Movement numbers therefore measure the Caller against scripted persona
  concession rules, not real movers.
- **Single vertical** (moving), single seed job spec, three personas.
- **Small n.** Three calls is evidence of mechanism, not a statistical claim.
- The AI-disclosure honesty check passed vacuously in the frozen set (no
  persona asked); the aggressive persona now always asks, but the frozen
  golden calls predate that change.
- See [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Rules the agent cannot break

Identical job description on every call; if asked whether it's an AI, it says
yes immediately; it never invents bids, inventory, or constraints; every call
ends with an itemised quote, a committed callback, or a documented decline;
quotes 30%+ below market are flagged as lowballs, not chased.

MIT licensed.
