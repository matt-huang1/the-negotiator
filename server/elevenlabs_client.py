"""Thin ElevenLabs Agents Platform client — outbound calls via imported Twilio number.

Docs: https://elevenlabs.io/docs/agents-platform  (check exact endpoint shape —
verify against current docs at hack time; this follows the Twilio outbound-call API.)
"""
import os

import httpx

BASE = "https://api.elevenlabs.io/v1/convai"


def _headers():
    return {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}


def start_outbound_call(to_number: str, dynamic_variables: dict) -> dict:
    """Place an outbound call from the Caller agent to `to_number`.

    dynamic_variables are available in the agent prompt as {{job_spec}},
    {{best_quote}}, {{call_id}}.
    """
    payload = {
        "agent_id": os.environ["ELEVENLABS_CALLER_AGENT_ID"],
        "agent_phone_number_id": os.environ["ELEVENLABS_PHONE_NUMBER_ID"],
        "to_number": to_number,
        "conversation_initiation_client_data": {
            "dynamic_variables": dynamic_variables,
        },
    }
    r = httpx.post(f"{BASE}/twilio/outbound-call", headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def get_conversation(conversation_id: str) -> dict:
    """Fetch transcript + metadata after the call (alternative to webhook)."""
    r = httpx.get(f"{BASE}/conversations/{conversation_id}", headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()
