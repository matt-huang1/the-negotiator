# RUNBOOK — running the pipeline

Two modes: **simulation** (agent-vs-agent in-platform, no telephony — how the
frozen results were produced) and **live telephony** (Twilio; requires an
account that can call your counterparty numbers — see README "Limitations").

## Simulation mode (works from a clean clone + your own keys)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # fill ELEVENLABS_API_KEY, OPENAI_API_KEY, BASE_URL
python -m scripts.provision agents          # creates Caller + honest counter-agent
# paste the printed agent IDs into .env
mkdir -p data/specs && cp scripts/seed_jobspec.json data/specs/demo.json
python -m scripts.simulate_call --job demo --persona honest
python -m server.quote_extractor
python -m benchmark.harness
```
`BASE_URL` must be an https URL at provision time (it's baked into the
`log_quote` webhook tool). In simulation, tools are mocked and the URL is never
called, so any https URL you control works. If it ever changes, PATCH the tool
(`/v1/convai/tools/{id}`) rather than re-creating agents.

## Live telephony mode
1. Run the FastAPI server and expose it (`uvicorn server.main:app --port 8000`
   plus a tunnel, e.g. a named Cloudflare tunnel); set `BASE_URL` to the
   public URL **before** provisioning.
2. Import two Twilio numbers (`python -m scripts.provision phone ...` — one
   outbound line, one `--assign-honest` inbound line) and fill the IDs in `.env`.
3. Store a confirmed spec via `POST /jobspec`, then
   `POST /calls/start?job_id=...&persona=honest`.
4. `POST /calls/<call_id>/sync_transcript` after hang-up, then extractor + harness.

## Reproduce the frozen scoreboard (no keys needed)
```bash
mkdir -p data/quotes && cp benchmark/golden_calls/quote-*.json data/quotes/
python -m benchmark.harness
```
