from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from grocery_agent.apple_notes import AppleNotesSyncPlanner
from grocery_agent.storage import JsonStore


@dataclass(frozen=True)
class BlueBubblesEvent:
    chat_id: str
    sender: str
    text: str


class GroceryMessageHandler:
    """Handle plain-language grocery requests from an iMessage group chat.

    The handler is intentionally platform-light: Hermes/BlueBubbles can own the
    live transport, while this class owns grocery-specific message behavior.
    """

    def __init__(self, store: JsonStore):
        self.store = store

    def handle(self, event: BlueBubblesEvent) -> str:
        text = event.text.strip()
        command, value = _parse_chat_command(text)

        if command == "add" and value:

            def add(agent):
                item = agent.add_request(value, requested_by=event.sender)
                return f"Added {item.name} to the grocery list."

            return self.store.update(add)

        if command == "remove" and value:

            def remove(agent):
                removed = agent.remove_item(value)
                return f"Removed {value.strip().lower()} from the grocery list." if removed else f"I couldn't find {value.strip().lower()} on the needed list."

            return self.store.update(remove)

        if command == "confirm" and value:

            def confirm(agent):
                confirmed = agent.confirm_item(value)
                return f"Confirmed {value.strip().lower()} for the shared note." if confirmed else f"I couldn't find a needed item matching {value.strip().lower()}."

            return self.store.update(confirm)

        if command == "list":
            return self.store.load().build_grocery_digest()

        if command == "apple_note":
            agent = self.store.load()
            planner = AppleNotesSyncPlanner()
            draft = planner.build_note_draft(agent)
            plan = planner.build_invite_plan(draft)
            invite_line = ", ".join(draft.invitees) if draft.invitees else "No invitees configured yet"
            return f"Apple Notes draft: {draft.title}\n{draft.body}\nInvitees: {invite_line}\nNext step: {plan.manual_steps[0]} Then use Share Note > Collaborate to invite them."

        return _help_text()


def parse_bluebubbles_webhook(payload: Mapping[str, Any]) -> BlueBubblesEvent | None:
    """Normalize a BlueBubbles webhook payload into a grocery chat event.

    BlueBubbles webhook shapes can vary slightly by server version. This parser
    accepts the documented nested `data.message` shape and a flatter fallback.
    Messages sent by the agent/Mac itself are ignored to avoid reply loops.
    """

    data = payload.get("data", {})
    message = data.get("message", data)
    if message.get("isFromMe") is True:
        return None

    text = message.get("text") or message.get("message") or ""
    if not str(text).strip():
        return None

    handle = message.get("handle") or data.get("handle") or {}
    sender = _sender_from_handle(handle) or message.get("address") or message.get("sender") or "unknown"
    chat_id = data.get("chatGuid") or message.get("chatGuid") or payload.get("chatGuid") or "unknown"
    return BlueBubblesEvent(chat_id=str(chat_id), sender=str(sender), text=str(text))


def _sender_from_handle(handle: object) -> str | None:
    if isinstance(handle, Mapping):
        address = handle.get("address")
        return str(address) if address else None
    if isinstance(handle, str):
        return handle
    return None


def _parse_chat_command(text: str) -> tuple[str, str | None]:
    normalized = _strip_wake_word(text)
    lowered = normalized.lower()
    for prefix, command in (("add ", "add"), ("remove ", "remove"), ("delete ", "remove"), ("confirm ", "confirm")):
        if lowered.startswith(prefix):
            return command, normalized[len(prefix) :].strip()

    if lowered in {"list", "grocery list", "what do we need?", "what do we need", "show list", "digest"}:
        return "list", None

    if lowered in {"apple note", "apple notes", "share note", "shared note", "notes plan", "note invite", "invite people"}:
        return "apple_note", None

    return "help", None


def _strip_wake_word(text: str) -> str:
    return re.sub(r"^@?(?:grocery|hermes)\b[\s:,-]*", "", text.strip(), count=1, flags=re.IGNORECASE).strip()


def _help_text() -> str:
    return "I can help with groceries. Try: add eggs, remove bananas, confirm milk, or what do we need?"
