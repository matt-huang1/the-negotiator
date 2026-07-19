"""FALLBACK PATH — agent-to-agent negotiation in-platform (no telephony).

Used when Twilio blocks real calls (see README "Telephony fallback"). The REAL
Caller agent negotiates against a simulated counterparty running the persona
prompt verbatim. Output transcript is schema-identical downstream: it lands in
data/transcripts/ and flows through quote_extractor -> harness unchanged.

Usage:  python -m scripts.simulate_call --job 05727657 --persona honest
"""
import argparse
import json
import os
import time
import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv

from server.elevenlabs_client import BASE, _headers

load_dotenv()
ROOT = Path(__file__).parent.parent
DATA = Path(os.getenv("DATA_DIR", "./data"))

PERSONA_FILES = {"aggressive": "aggressive_mover.md", "evasive": "evasive_mover.md",
                 "honest": "honest_mover.md"}
GREETINGS = {"honest": "Good afternoon, Fairway Removals, Priya speaking — how can I help?",
             "aggressive": "Yeah, hello, this is Big Move Logistics.",
             "evasive": "Hello? ...sorry, who's this?"}


def best_quote(job_id: str):
    quotes = [json.loads(p.read_text()) for p in (DATA / "quotes").glob("*.json")]
    quotes = [q for q in quotes if q.get("call_id", "").startswith(job_id)
              and q.get("binding") and q.get("total_gbp")]
    return min(quotes, key=lambda q: q["total_gbp"]) if quotes else None


def simulate(job_id: str, persona: str, turns: int) -> str:
    spec = json.loads((DATA / "specs" / f"{job_id}.json").read_text())
    best = best_quote(job_id)
    call_id = f"{job_id}-{persona}-{str(uuid.uuid4())[:4]}"
    persona_prompt = (ROOT / "prompts" / "counter_agents" / PERSONA_FILES[persona]).read_text()

    payload = {
        "simulation_specification": {
            "simulated_user_config": {
                "first_message": GREETINGS[persona],
                "language": "en",
                "prompt": {"prompt": persona_prompt},
            },
            "dynamic_variables": {
                "job_spec": json.dumps(spec),
                "best_quote": json.dumps(best) if best else "NONE — do not claim a competing bid",
                "call_id": call_id,
            },
        },
        "new_turns_limit": turns,
    }
    (DATA / "calls" / f"{call_id}.json").write_text(json.dumps(
        {"call_id": call_id, "job_id": job_id, "persona": persona, "mode": "simulation",
         "started_at": time.time(), "best_quote_at_call_time": best, "price_events": []}, indent=2))

    agent_id = os.environ["ELEVENLABS_CALLER_AGENT_ID"]
    r = httpx.post(f"{BASE}/agents/{agent_id}/simulate-conversation", headers=_headers(),
                   json=payload, timeout=600)
    r.raise_for_status()
    body = r.json()
    (DATA / "transcripts" / f"{call_id}.json").write_text(json.dumps(body, indent=2))
    print(f"saved data/transcripts/{call_id}.json "
          f"({len(body.get('simulated_conversation', []))} turns)")
    return call_id


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--persona", required=True, choices=sorted(PERSONA_FILES))
    ap.add_argument("--turns", type=int, default=40)
    args = ap.parse_args()
    simulate(args.job, args.persona, args.turns)
