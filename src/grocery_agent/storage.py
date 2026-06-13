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
        agent = GroceryAgent(config=config)
        agent.items = [GroceryItem(**item) for item in data.get("items", [])]
        return agent

    def save(self, agent: GroceryAgent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "config": asdict(agent.config),
            "items": [asdict(item) for item in agent.items],
        }
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
