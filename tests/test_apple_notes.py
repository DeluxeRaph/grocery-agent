from grocery_agent.apple_notes import AppleNotesInvitePlan, AppleNotesNoteDraft, AppleNotesSyncPlanner
from grocery_agent.core import GroceryAgent, HouseholdConfig


def test_apple_notes_draft_uses_confirmed_items_and_configured_invitees():
    agent = GroceryAgent(
        HouseholdConfig(
            household_name="Farm House",
            area="90210",
            radius_miles=10,
            shopping_days=["saturday"],
            favorite_stores=["Kroger"],
            note_invitees=["farmer@icloud.com", "+155****4567"],
        )
    )
    milk = agent.add_request("2 gallons of whole milk", requested_by="Farmer")
    agent.add_request("chips", requested_by="Cloud")
    agent.confirm_item(milk.id)

    draft = AppleNotesSyncPlanner().build_note_draft(agent)

    assert draft == AppleNotesNoteDraft(
        title="Farm House Grocery List",
        body="# Grocery List\n\n- whole milk (2 gallons)",
        invitees=["farmer@icloud.com", "+155****4567"],
    )


def test_apple_notes_invite_plan_supports_agent_or_manual_invites():
    draft = AppleNotesNoteDraft(
        title="Farm House Grocery List",
        body="# Grocery List\n\n- milk",
        invitees=["farmer@icloud.com", "cloud@icloud.com"],
    )

    plan = AppleNotesSyncPlanner().build_invite_plan(draft)

    assert isinstance(plan, AppleNotesInvitePlan)
    assert plan.can_auto_invite is False
    assert "Apple Notes has no public cross-platform invite API" in plan.limitation
    assert "Open Notes on the Mac/iPhone signed into iCloud." in plan.manual_steps[0]
    assert "farmer@icloud.com, cloud@icloud.com" in "\n".join(plan.manual_steps)
    assert plan.agent_handoff["title"] == "Farm House Grocery List"
    assert plan.agent_handoff["invitees"] == ["farmer@icloud.com", "cloud@icloud.com"]


def test_apple_notes_shortcuts_payload_contains_title_body_and_invitees():
    draft = AppleNotesNoteDraft(
        title="Roommates Grocery List",
        body="# Grocery List\n\n- eggs",
        invitees=["roommate@example.com"],
    )

    payload = AppleNotesSyncPlanner().build_shortcuts_payload(draft)

    assert payload == {
        "action": "create_or_update_shared_apple_note",
        "title": "Roommates Grocery List",
        "body": "# Grocery List\n\n- eggs",
        "invitees": ["roommate@example.com"],
    }
