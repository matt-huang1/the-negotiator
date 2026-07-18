"""FastAPI orchestration: job specs, outbound calls, quote events, transcripts.

File-based storage (DATA_DIR) — deliberately no DB so one person can run it.
Run: uvicorn server.main:app --reload --port 8000
"""
import json
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request

from server.elevenlabs_client import get_conversation, start_outbound_call

load_dotenv()
DATA = Path(os.getenv("DATA_DIR", "./data"))
for sub in ("specs", "calls", "quotes", "transcripts"):
    (DATA / sub).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="The Negotiator")

COUNTERPARTIES = {
    "aggressive": os.getenv("COUNTER_AGGRESSIVE_NUMBER"),
    "evasive": os.getenv("COUNTER_EVASIVE_NUMBER"),
    "honest": os.getenv("COUNTER_HONEST_NUMBER"),
}


def _save(kind: str, obj_id: str, payload: dict) -> None:
    (DATA / kind / f"{obj_id}.json").write_text(json.dumps(payload, indent=2))


def _load(kind: str, obj_id: str) -> dict:
    p = DATA / kind / f"{obj_id}.json"
    if not p.exists():
        raise HTTPException(404, f"{kind}/{obj_id} not found")
    return json.loads(p.read_text())


@app.post("/jobspec")
async def save_job_spec(request: Request):
    """Webhook target for the Estimator agent's save_job_spec tool."""
    spec = await request.json()
    if not spec.get("confirmed_by_user"):
        raise HTTPException(400, "Spec not confirmed by user — refusing to store as callable.")
    spec.setdefault("job_id", str(uuid.uuid4())[:8])
    _save("specs", spec["job_id"], spec)
    return {"job_id": spec["job_id"]}


@app.post("/calls/start")
async def start_call(job_id: str, persona: str):
    """Kick off one outbound call: Caller agent -> counter-agent's number.

    best_quote (cheapest binding quote so far for this job) is injected as
    leverage — the agent may ONLY cite bids that exist. This is the honesty rule
    enforced structurally, not just by prompt.
    """
    if persona not in COUNTERPARTIES or not COUNTERPARTIES[persona]:
        raise HTTPException(400, f"No number configured for persona '{persona}'")
    spec = _load("specs", job_id)
    best = _best_quote(job_id)

    call_id = f"{job_id}-{persona}-{str(uuid.uuid4())[:4]}"
    result = start_outbound_call(
        to_number=COUNTERPARTIES[persona],
        dynamic_variables={
            "job_spec": json.dumps(spec),
            "best_quote": json.dumps(best) if best else "NONE — do not claim a competing bid",
            "call_id": call_id,
        },
    )
    _save("calls", call_id, {"call_id": call_id, "job_id": job_id, "persona": persona,
                             "started_at": time.time(), "elevenlabs": result, "price_events": []})
    return {"call_id": call_id, **result}


@app.post("/calls/{call_id}/quote_event")
async def log_quote_event(call_id: str, request: Request):
    """Webhook target for the Caller agent's log_quote tool (mid-call)."""
    event = await request.json()
    call = _load("calls", call_id)
    event.setdefault("t_seconds", round(time.time() - call.get("started_at", time.time()), 1))
    call["price_events"].append(event)
    _save("calls", call_id, call)
    return {"ok": True, "events": len(call["price_events"])}


@app.post("/calls/{call_id}/transcript")
async def save_transcript(call_id: str, request: Request):
    """Post-call webhook from ElevenLabs (conversation ended)."""
    body = await request.json()
    (DATA / "transcripts" / f"{call_id}.json").write_text(json.dumps(body, indent=2))
    # TODO: trigger quote_extractor here (or run it as a batch step)
    return {"ok": True}


@app.post("/calls/{call_id}/sync_transcript")
async def sync_transcript(call_id: str):
    """Pull the transcript from ElevenLabs and save it (poll until status=done).

    Simpler than the workspace-level post-call webhook: no dashboard config,
    works the moment the call ends.
    """
    call = _load("calls", call_id)
    conversation_id = call.get("elevenlabs", {}).get("conversation_id")
    if not conversation_id:
        raise HTTPException(400, "No conversation_id stored for this call")
    convo = get_conversation(conversation_id)
    status = convo.get("status")
    if status not in ("done", "failed"):
        return {"ok": False, "status": status, "hint": "call still in progress — retry shortly"}
    (DATA / "transcripts" / f"{call_id}.json").write_text(json.dumps(convo, indent=2))
    return {"ok": True, "status": status, "turns": len(convo.get("transcript", [])),
            "path": f"data/transcripts/{call_id}.json"}


@app.get("/jobs/{job_id}/quotes")
async def list_quotes(job_id: str):
    quotes = []
    for p in (DATA / "quotes").glob("*.json"):
        q = json.loads(p.read_text())
        if q.get("call_id", "").startswith(job_id):
            quotes.append(q)
    return sorted(quotes, key=lambda q: q.get("total_gbp") or 9e9)


def _best_quote(job_id: str):
    """Cheapest BINDING quote so far — the only leverage the agent may cite."""
    quotes = [json.loads(p.read_text()) for p in (DATA / "quotes").glob("*.json")]
    quotes = [q for q in quotes if q.get("call_id", "").startswith(job_id)
              and q.get("binding") and q.get("total_gbp")]
    return min(quotes, key=lambda q: q["total_gbp"]) if quotes else None
