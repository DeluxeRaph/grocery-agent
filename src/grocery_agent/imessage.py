from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

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
        agent = self.store.load()

        if command == "add" and value:
            item = agent.add_request(value, requested_by=event.sender)
            self.store.save(agent)
            return f"Added {item.name} to the grocery list."

        if command == "remove" and value:
            removed = agent.remove_item(value)
            self.store.save(agent)
            return f"Removed {value.strip().lower()} from the grocery list." if removed else f"I couldn't find {value.strip().lower()} on the needed list."

        if command == "confirm" and value:
            confirmed = agent.confirm_item(value)
            self.store.save(agent)
            return f"Confirmed {value.strip().lower()} for the shared note." if confirmed else f"I couldn't find a needed item matching {value.strip().lower()}."

        if command == "list":
            return agent.build_grocery_digest()

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
    sender = handle.get("address") or message.get("address") or message.get("sender") or "unknown"
    chat_id = data.get("chatGuid") or message.get("chatGuid") or payload.get("chatGuid") or "unknown"
    return BlueBubblesEvent(chat_id=str(chat_id), sender=str(sender), text=str(text))


def _parse_chat_command(text: str) -> tuple[str, str | None]:
    lowered = text.strip().lower()
    for prefix, command in (("add ", "add"), ("remove ", "remove"), ("delete ", "remove"), ("confirm ", "confirm")):
        if lowered.startswith(prefix):
            return command, text.strip()[len(prefix) :].strip()

    if lowered in {"list", "grocery list", "what do we need?", "what do we need", "show list", "digest"}:
        return "list", None

    return "help", None


def _help_text() -> str:
    return "I can help with groceries. Try: add eggs, remove bananas, confirm milk, or what do we need?"
