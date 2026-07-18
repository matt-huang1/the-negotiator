"""Thin ElevenLabs Agents Platform client — outbound calls via imported Twilio number.

Endpoints verified against the live OpenAPI spec (api.elevenlabs.io/openapi.json)
on 2026-07-18: outbound call, conversation fetch, agent/tool create, phone import.
"""
import os
from typing import Optional

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


def create_tool(tool_config: dict) -> str:
    """Create a workspace tool (e.g. the log_quote webhook); returns tool id."""
    r = httpx.post(f"{BASE}/tools", headers=_headers(), json={"tool_config": tool_config}, timeout=30)
    r.raise_for_status()
    return r.json()["id"]


def create_agent(name: str, conversation_config: dict) -> str:
    """Create an agent; returns agent id."""
    r = httpx.post(f"{BASE}/agents/create", headers=_headers(),
                   json={"name": name, "conversation_config": conversation_config}, timeout=30)
    r.raise_for_status()
    return r.json()["agent_id"]


def import_twilio_number(phone_number: str, label: str, sid: str, token: str,
                         agent_id: Optional[str] = None) -> str:
    """Import a Twilio number; assigning agent_id makes it answer inbound calls
    as that agent. Returns phone_number_id."""
    payload = {"provider": "twilio", "phone_number": phone_number, "label": label,
               "sid": sid, "token": token}
    if agent_id:
        payload["agent_id"] = agent_id
    r = httpx.post(f"{BASE}/phone-numbers", headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["phone_number_id"]
