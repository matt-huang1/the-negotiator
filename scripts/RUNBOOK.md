# RUNBOOK — first real call, end to end

Prereqs: `.env` filled with `ELEVENLABS_API_KEY`, `TWILIO_ACCOUNT_SID`,
`TWILIO_AUTH_TOKEN`, and TWO Twilio numbers (outbound line for the Caller,
inbound line for the counter-agent — a second number is ~$1/mo on Twilio).

## 1. Server + tunnel (two terminals)
```bash
uvicorn server.main:app --reload --port 8000
ngrok http 8000        # or: cloudflared tunnel --url http://localhost:8000
```
Put the public URL in `.env` as `BASE_URL=https://xxxx.ngrok-free.app`
(no trailing slash). The log_quote webhook tool bakes this URL in at provision
time — if the tunnel URL changes, re-run provisioning or use a reserved domain.

## 2. Provision (once)
```bash
python -m scripts.provision agents
# copy the two printed IDs into .env
python -m scripts.provision phone --number +44XXXX --label caller-outbound
# copy ELEVENLABS_PHONE_NUMBER_ID into .env
python -m scripts.provision phone --number +44YYYY --label honest-inbound --assign-honest
# copy COUNTER_HONEST_NUMBER into .env
python -m scripts.provision check   # verify everything exists
```
Restart uvicorn after editing `.env`.

## 3. One call
```bash
curl -s -X POST $BASE_URL/jobspec -H 'content-type: application/json' \
  -d @scripts/seed_jobspec.json
# -> {"job_id": "abc12345"}

curl -s -X POST "$BASE_URL/calls/start?job_id=abc12345&persona=honest"
# -> {"call_id": "abc12345-honest-xxxx", "conversation_id": ...}
```
Listen in: ElevenLabs dashboard → Agents → Calls shows the live conversation.

## 4. Transcript + scoreboard
```bash
curl -s -X POST $BASE_URL/calls/<call_id>/sync_transcript   # retry until status=done
python -m server.quote_extractor
python -m benchmark.harness
```

## Fallback (Twilio blocks us >45 min)
Skip phone import; in the ElevenLabs dashboard use "Test agent" /
agent-to-agent simulation, export the transcript JSON into
`data/transcripts/<call_id>.json` manually, and disclose the fallback in the
demo. The rest of the pipeline (extractor → harness → report) is unchanged.
