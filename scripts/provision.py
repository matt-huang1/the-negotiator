"""Provision ElevenLabs agents, the log_quote webhook tool, and Twilio numbers.

Usage:
  python -m scripts.provision agents              # log_quote tool + Caller + honest counter-agent
  python -m scripts.provision phone --number +447... --label caller-outbound
  python -m scripts.provision phone --number +447... --label honest-inbound --assign-honest
  python -m scripts.provision check               # sanity: list agents + numbers for this key

Prints the .env lines to copy after each step. Idempotence is manual: run
`check` first if unsure what already exists — this script always creates new
resources, never updates.
"""
import argparse
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

from server.elevenlabs_client import BASE, _headers, create_agent, create_tool, import_twilio_number

load_dotenv()
ROOT = Path(__file__).parent.parent
LLM = os.getenv("ELEVENLABS_LLM", "claude-sonnet-4-5")

# Matches schema/quote.schema.json price_events[].trigger — keep in sync.
TRIGGERS = ["opening_quote", "itemisation", "leverage_competing_bid",
            "leverage_flexibility", "leverage_bundling", "counterparty_pressure", "final_offer"]


def make_log_quote_tool(base_url: str) -> str:
    # {call_id} in the URL is filled from the call's dynamic variables (set at
    # /calls/start), NOT by the LLM — the event always lands on the right call.
    return create_tool({
        "type": "webhook",
        "name": "log_quote",
        "description": ("Log a price the moving company just stated. Call this immediately "
                        "EVERY time the counterparty states a total price for the move, "
                        "including revised prices during negotiation."),
        "response_timeout_secs": 10,
        "api_schema": {
            "url": f"{base_url}/calls/{{call_id}}/quote_event",
            "method": "POST",
            "path_params_schema": {
                "call_id": {"type": "string", "dynamic_variable": "call_id"},
            },
            "request_body_schema": {
                "type": "object",
                "required": ["price_gbp", "trigger"],
                "properties": {
                    "price_gbp": {"type": "number",
                                  "description": "The total price in GBP the counterparty just stated."},
                    "trigger": {"type": "string", "enum": TRIGGERS,
                                "description": "What caused this price: their opening quote, an "
                                               "itemisation, one of YOUR leverage lines (competing bid / "
                                               "date flexibility / bundling), their own pressure tactic, "
                                               "or the final offer."},
                    "transcript_snippet": {"type": "string",
                                           "description": "Short verbatim quote of the counterparty "
                                                          "stating this price."},
                    "binding": {"type": "boolean",
                                "description": "True if they said this quote is binding/fixed."},
                },
            },
        },
    })


def provision_agents(base_url: str) -> None:
    tool_id = make_log_quote_tool(base_url)
    print(f"log_quote tool: {tool_id}  (webhook -> {base_url}/calls/{{call_id}}/quote_event)")

    caller_prompt = (ROOT / "prompts" / "caller_agent.md").read_text()
    caller_id = create_agent("Negotiator — Caller", {
        "agent": {
            # Empty: the counterparty answers the phone and greets first.
            "first_message": "",
            "language": "en",
            "prompt": {"prompt": caller_prompt, "llm": LLM, "tool_ids": [tool_id]},
        },
    })
    print(f"Caller agent: {caller_id}")

    honest_prompt = (ROOT / "prompts" / "counter_agents" / "honest_mover.md").read_text()
    honest_id = create_agent("Counter — Honest (Priya, Fairway Removals)", {
        "agent": {
            "first_message": "Good afternoon, Fairway Removals, Priya speaking — how can I help?",
            "language": "en",
            "prompt": {"prompt": honest_prompt, "llm": LLM},
        },
    })
    print(f"Honest counter-agent: {honest_id}")

    print("\nAdd to .env:")
    print(f"ELEVENLABS_CALLER_AGENT_ID={caller_id}")
    print(f"ELEVENLABS_COUNTER_HONEST_AGENT_ID={honest_id}")


def provision_phone(number: str, label: str, assign_honest: bool) -> None:
    agent_id = os.getenv("ELEVENLABS_COUNTER_HONEST_AGENT_ID") if assign_honest else None
    if assign_honest and not agent_id:
        sys.exit("Set ELEVENLABS_COUNTER_HONEST_AGENT_ID in .env first (run `agents`).")
    phone_id = import_twilio_number(
        number, label,
        sid=os.environ["TWILIO_ACCOUNT_SID"], token=os.environ["TWILIO_AUTH_TOKEN"],
        agent_id=agent_id,
    )
    print(f"Imported {number} ({label}): {phone_id}")
    print("\nAdd to .env:")
    if assign_honest:
        print(f"COUNTER_HONEST_NUMBER={number}")
    else:
        print(f"ELEVENLABS_PHONE_NUMBER_ID={phone_id}")


def check() -> None:
    for path, key in (("/agents", "agents"), ("/phone-numbers", None)):
        r = httpx.get(f"{BASE}{path}", headers=_headers(), timeout=30)
        r.raise_for_status()
        items = r.json()[key] if key else r.json()
        print(f"{path}:")
        for it in items:
            print(f"  {it.get('agent_id') or it.get('phone_number_id')}  "
                  f"{it.get('name') or it.get('label')}  {it.get('phone_number', '')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("agents")
    p = sub.add_parser("phone")
    p.add_argument("--number", required=True, help="E.164, e.g. +447700900123")
    p.add_argument("--label", required=True)
    p.add_argument("--assign-honest", action="store_true",
                   help="answer inbound calls as the honest counter-agent")
    sub.add_parser("check")
    args = ap.parse_args()

    base_url = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
    if args.cmd == "agents":
        if "localhost" in base_url or "127.0.0.1" in base_url:
            sys.exit(f"BASE_URL is {base_url} — ElevenLabs can't reach localhost. "
                     "Start the tunnel first and set BASE_URL to the public URL.")
        provision_agents(base_url)
    elif args.cmd == "phone":
        provision_phone(args.number, args.label, args.assign_honest)
    else:
        check()
