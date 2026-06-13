from datetime import date

from grocery_agent.core import GroceryAgent, GroceryItem, HouseholdConfig


def test_add_item_normalizes_name_and_tracks_requester():
    config = HouseholdConfig(
        household_name="Farm House",
        area="90210",
        radius_miles=10,
        shopping_days=["saturday"],
        favorite_stores=["Kroger"],
    )
    agent = GroceryAgent(config=config)

    item = agent.add_request(" Add 2 gallons of Whole Milk ", requested_by="Farmer")

    assert item.name == "whole milk"
    assert item.quantity == "2 gallons"
    assert item.category == "dairy"
    assert item.requested_by == "Farmer"
    assert agent.list_needed_items() == [item]


def test_remove_item_marks_item_done_without_deleting_history():
    agent = GroceryAgent.default_for(area="90210")
    item = agent.add_request("eggs", requested_by="Cloud")

    removed = agent.remove_item("eggs")

    assert removed is True
    assert agent.list_needed_items() == []
    assert agent.items[0].id == item.id
    assert agent.items[0].status == "removed"


def test_grocery_digest_groups_items_by_category_and_mentions_shopping_day():
    agent = GroceryAgent(
        config=HouseholdConfig(
            household_name="Roommates",
            area="10001",
            radius_miles=5,
            shopping_days=["monday", "thursday"],
            favorite_stores=["Trader Joe's", "Target"],
        )
    )
    agent.add_request("eggs", requested_by="Ari")
    agent.add_request("bananas", requested_by="Bea")

    digest = agent.build_grocery_digest(today=date(2026, 6, 15))

    assert "Roommates grocery list" in digest
    assert "Shopping day today" in digest
    assert "Trader Joe's, Target" in digest
    assert "Dairy: eggs" in digest
    assert "Produce: bananas" in digest


def test_deal_scan_matches_current_list_and_ranks_by_savings_then_distance():
    agent = GroceryAgent.default_for(area="90210")
    agent.add_request("milk", requested_by="Farmer")
    agent.add_request("eggs", requested_by="Farmer")

    deals = agent.find_matching_deals(
        [
            {"store": "Far Store", "item": "milk", "price": 3.50, "original_price": 5.00, "distance_miles": 8.0},
            {"store": "Near Store", "item": "milk", "price": 3.75, "original_price": 5.00, "distance_miles": 1.0},
            {"store": "Bakery", "item": "flour", "price": 2.00, "original_price": 3.00, "distance_miles": 1.0},
            {"store": "Egg Mart", "item": "eggs", "price": 2.25, "original_price": 4.25, "distance_miles": 4.0},
        ]
    )

    assert [deal.item for deal in deals] == ["eggs", "milk", "milk"]
    assert deals[0].store == "Egg Mart"
    assert deals[0].savings == 2.00


def test_confirmed_items_export_to_shared_note_text():
    agent = GroceryAgent.default_for(area="90210")
    milk = agent.add_request("milk", requested_by="Farmer")
    agent.add_request("chips", requested_by="Cloud")

    agent.confirm_item(milk.id)
    note = agent.export_confirmed_note()

    assert "# Grocery List" in note
    assert "- milk" in note
    assert "chips" not in note
