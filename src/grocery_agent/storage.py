from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from grocery_agent.core import GroceryAgent, GroceryItem, HouseholdConfig


class JsonStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self, default_area: str = "00000") -> GroceryAgent:
        if not self.path.exists():
            return GroceryAgent.default_for(area=default_area)

        data = json.loads(self.path.read_text())
        config = HouseholdConfig(**data["config"])
        items = [GroceryItem(**item) for item in data.get("items", [])]
        agent = GroceryAgent(config=config, next_item_number=data.get("next_item_id", _next_item_number(items)))
        agent.items = items
        return agent

    def save(self, agent: GroceryAgent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "config": asdict(agent.config),
            "items": [asdict(item) for item in agent.items],
            "next_item_id": agent._next_item_number,
        }
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _next_item_number(items: list[GroceryItem]) -> int:
    numbers: list[int] = []
    for item in items:
        prefix, _, suffix = item.id.partition("_")
        if prefix == "item" and suffix.isdigit():
            numbers.append(int(suffix))
    return max(numbers, default=0) + 1
