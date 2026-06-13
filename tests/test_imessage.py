from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from grocery_agent.core import GroceryAgent, HouseholdConfig
from grocery_agent.imessage import BlueBubblesEvent, GroceryMessageHandler, parse_bluebubbles_webhook
from grocery_agent.storage import JsonStore


def _seed_store(path: Path) -> None:
    JsonStore(path).save(
        GroceryAgent(
            HouseholdConfig(
                household_name="Farm House",
                area="90210",
                radius_miles=10,
                shopping_days=["saturday"],
                favorite_stores=["Kroger"],
            )
        )
    )


def test_imessage_add_message_updates_grocery_list_and_returns_plain_text(tmp_path: Path):
    state = tmp_path / "state.json"
    _seed_store(state)
    handler = GroceryMessageHandler(JsonStore(state))

    response = handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="farmer@icloud.com", text="add eggs"))

    loaded = JsonStore(state).load()
    assert response == "Added eggs to the grocery list."
    assert loaded.items[0].name == "eggs"
    assert loaded.items[0].requested_by == "farmer@icloud.com"


def test_imessage_list_message_returns_current_digest(tmp_path: Path):
    state = tmp_path / "state.json"
    _seed_store(state)
    handler = GroceryMessageHandler(JsonStore(state))
    handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="a@icloud.com", text="add milk"))

    response = handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="b@icloud.com", text="what do we need?"))

    assert "Farm House grocery list" in response
    assert "Dairy: milk" in response


def test_imessage_remove_and_confirm_commands_use_natural_chat_language(tmp_path: Path):
    state = tmp_path / "state.json"
    _seed_store(state)
    handler = GroceryMessageHandler(JsonStore(state))
    handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="a@icloud.com", text="add bananas"))
    handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="a@icloud.com", text="add milk"))

    remove_response = handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="a@icloud.com", text="remove bananas"))
    confirm_response = handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="a@icloud.com", text="confirm milk"))

    loaded = JsonStore(state).load()
    assert remove_response == "Removed bananas from the grocery list."
    assert confirm_response == "Confirmed milk for the shared note."
    assert [item.status for item in loaded.items] == ["removed", "confirmed"]


def test_imessage_unknown_message_returns_help_without_mutating_state(tmp_path: Path):
    state = tmp_path / "state.json"
    _seed_store(state)
    handler = GroceryMessageHandler(JsonStore(state))

    response = handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="a@icloud.com", text="hello there"))

    assert "Try: add eggs" in response
    assert JsonStore(state).load().items == []


def test_imessage_accepts_grocery_wake_word_before_mutating_commands(tmp_path: Path):
    state = tmp_path / "state.json"
    _seed_store(state)
    handler = GroceryMessageHandler(JsonStore(state))

    add_response = handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="a@icloud.com", text="@grocery: add milk"))
    remove_response = handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="a@icloud.com", text="grocery remove milk"))

    loaded = JsonStore(state).load()
    assert add_response == "Added milk to the grocery list."
    assert remove_response == "Removed milk from the grocery list."
    assert [item.name for item in loaded.items] == ["milk"]
    assert [item.status for item in loaded.items] == ["removed"]


def test_imessage_accepts_grocery_wake_word_before_list_commands(tmp_path: Path):
    state = tmp_path / "state.json"
    _seed_store(state)
    handler = GroceryMessageHandler(JsonStore(state))
    handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="a@icloud.com", text="add milk"))

    response = handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="b@icloud.com", text="@grocery what do we need?"))

    assert "Farm House grocery list" in response
    assert "Dairy: milk" in response


def test_imessage_unknown_grocery_wake_word_message_returns_help_without_mutating_state(tmp_path: Path):
    state = tmp_path / "state.json"
    _seed_store(state)
    handler = GroceryMessageHandler(JsonStore(state))

    response = handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender="a@icloud.com", text="@grocery random chatter"))

    assert "Try: add eggs" in response
    assert JsonStore(state).load().items == []


def test_imessage_concurrent_adds_preserve_every_message_with_unique_ids(tmp_path: Path):
    state = tmp_path / "state.json"
    _seed_store(state)
    handler = GroceryMessageHandler(JsonStore(state))
    item_count = 20
    start = Barrier(item_count)

    def add_item(index: int) -> str:
        start.wait(timeout=5)
        return handler.handle(BlueBubblesEvent(chat_id="chat-guid", sender=f"sender{index}@icloud.com", text=f"add item{index}"))

    with ThreadPoolExecutor(max_workers=item_count) as executor:
        responses = list(executor.map(add_item, range(item_count)))

    loaded = JsonStore(state).load()
    names = {item.name for item in loaded.items}
    ids = [item.id for item in loaded.items]

    assert all(response.startswith("Added item") for response in responses)
    assert names == {f"item{index}" for index in range(item_count)}
    assert len(ids) == item_count
    assert len(set(ids)) == item_count


def test_bluebubbles_webhook_payload_parses_group_chat_message():
    payload = {
        "type": "new-message",
        "data": {
            "chatGuid": "iMessage;+;chat123",
            "message": {
                "text": "add tortillas",
                "handle": {"address": "+15551234567"},
                "isFromMe": False,
            },
        },
    }

    event = parse_bluebubbles_webhook(payload)

    assert event == BlueBubblesEvent(chat_id="iMessage;+;chat123", sender="+15551234567", text="add tortillas")


def test_bluebubbles_webhook_payload_accepts_string_handle_shape():
    payload = {
        "data": {
            "chatGuid": "chat",
            "message": {"text": "add milk", "handle": "+15555550123", "isFromMe": False},
        }
    }

    event = parse_bluebubbles_webhook(payload)

    assert event == BlueBubblesEvent(chat_id="chat", sender="+15555550123", text="add milk")


def test_bluebubbles_parser_ignores_messages_sent_by_the_agent():
    payload = {
        "data": {
            "chatGuid": "chat",
            "message": {"text": "add milk", "handle": {"address": "me"}, "isFromMe": True},
        }
    }

    assert parse_bluebubbles_webhook(payload) is None
