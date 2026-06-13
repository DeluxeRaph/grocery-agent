from pathlib import Path

from grocery_agent.core import GroceryAgent, HouseholdConfig
from grocery_agent.imessage import BlueBubblesEvent, GroceryMessageHandler
from grocery_agent.storage import JsonStore


def test_imessage_share_note_returns_apple_notes_invite_plan(tmp_path: Path):
    state = tmp_path / "state.json"
    agent = GroceryAgent(
        HouseholdConfig(
            household_name="Farm House",
            area="90210",
            radius_miles=10,
            shopping_days=["saturday"],
            favorite_stores=["Kroger"],
            note_invitees=["farmer@icloud.com"],
        )
    )
    milk = agent.add_request("milk", requested_by="Farmer")
    agent.confirm_item(milk.id)
    JsonStore(state).save(agent)

    response = GroceryMessageHandler(JsonStore(state)).handle(
        BlueBubblesEvent(chat_id="chat-guid", sender="farmer@icloud.com", text="@grocery share note")
    )

    assert "Apple Notes draft: Farm House Grocery List" in response
    assert "- milk" in response
    assert "Invitees: farmer@icloud.com" in response
    assert "Share Note > Collaborate" in response
