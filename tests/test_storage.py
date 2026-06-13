import json
from pathlib import Path

from grocery_agent.core import GroceryAgent, HouseholdConfig
from grocery_agent.storage import JsonStore


def test_json_store_round_trips_household_and_items(tmp_path: Path):
    path = tmp_path / "state.json"
    agent = GroceryAgent(
        config=HouseholdConfig(
            household_name="Family",
            area="30301",
            radius_miles=7,
            shopping_days=["friday"],
            favorite_stores=["Aldi"],
            dietary_preferences=["vegetarian"],
        )
    )
    item = agent.add_request("tofu", requested_by="Farmer")
    agent.confirm_item(item.id)

    JsonStore(path).save(agent)
    loaded = JsonStore(path).load()

    assert loaded.config.household_name == "Family"
    assert loaded.config.area == "30301"
    assert loaded.items[0].name == "tofu"
    assert loaded.items[0].status == "confirmed"


def test_json_store_bootstraps_default_agent_when_file_missing(tmp_path: Path):
    loaded = JsonStore(tmp_path / "missing.json").load(default_area="60601")

    assert loaded.config.area == "60601"
    assert loaded.config.household_name == "Grocery Agent"


def test_json_store_writes_portable_json_shape(tmp_path: Path):
    path = tmp_path / "state.json"
    agent = GroceryAgent.default_for(area="90210")
    agent.add_request("milk", requested_by="Farmer")

    JsonStore(path).save(agent)

    data = json.loads(path.read_text())
    assert sorted(data) == ["config", "items"]
    assert data["config"]["area"] == "90210"
    assert data["items"][0]["name"] == "milk"
