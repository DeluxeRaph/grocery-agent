from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Mapping


_CATEGORY_KEYWORDS = {
    "dairy": {"milk", "cheese", "yogurt", "eggs", "butter", "cream"},
    "produce": {"banana", "bananas", "apple", "apples", "lettuce", "tomato", "tomatoes", "onion", "onions"},
    "meat": {"chicken", "beef", "turkey", "pork", "fish", "salmon"},
    "bakery": {"bread", "bagels", "tortillas", "buns"},
    "pantry": {"rice", "beans", "pasta", "flour", "sugar", "cereal", "chips", "salsa"},
}


@dataclass(frozen=True)
class HouseholdConfig:
    household_name: str
    area: str
    radius_miles: int
    shopping_days: list[str]
    favorite_stores: list[str]
    budget_mode: str = "balanced"
    dietary_preferences: list[str] = field(default_factory=list)


@dataclass
class GroceryItem:
    id: str
    name: str
    quantity: str | None
    category: str
    requested_by: str
    status: str = "needed"


@dataclass(frozen=True)
class Deal:
    store: str
    item: str
    price: float
    original_price: float
    distance_miles: float

    @property
    def savings(self) -> float:
        return round(self.original_price - self.price, 2)


class GroceryAgent:
    def __init__(self, config: HouseholdConfig, next_item_number: int = 1):
        self.config = config
        self.items: list[GroceryItem] = []
        self._next_item_number = next_item_number

    @classmethod
    def default_for(cls, area: str) -> "GroceryAgent":
        return cls(
            config=HouseholdConfig(
                household_name="Grocery Agent",
                area=area,
                radius_miles=10,
                shopping_days=["saturday"],
                favorite_stores=[],
            )
        )

    def add_request(self, text: str, requested_by: str) -> GroceryItem:
        quantity, name = _parse_request(text)
        item = GroceryItem(
            id=self._next_item_id(),
            name=name,
            quantity=quantity,
            category=_categorize(name),
            requested_by=requested_by,
        )
        self.items.append(item)
        return item

    def _next_item_id(self) -> str:
        item_id = f"item_{self._next_item_number}"
        self._next_item_number += 1
        return item_id

    def remove_item(self, name: str) -> bool:
        target = _normalize_name(name)
        for item in self.items:
            if item.status == "needed" and item.name == target:
                item.status = "removed"
                return True
        return False

    def confirm_item(self, item_id_or_name: str) -> bool:
        target = _normalize_name(item_id_or_name)
        for item in self.items:
            if (item.id == item_id_or_name or item.name == target) and item.status == "needed":
                item.status = "confirmed"
                return True
        return False

    def list_needed_items(self) -> list[GroceryItem]:
        return [item for item in self.items if item.status == "needed"]

    def build_grocery_digest(self, today: date | None = None) -> str:
        today = today or date.today()
        day_name = today.strftime("%A").lower()
        shopping_line = "Shopping day today" if day_name in self.config.shopping_days else f"Next shopping days: {', '.join(self.config.shopping_days)}"
        stores = ", ".join(self.config.favorite_stores) or "No favorite stores configured yet"

        groups: dict[str, list[str]] = {}
        for item in self.list_needed_items():
            groups.setdefault(item.category.title(), []).append(item.name)

        lines = [
            f"{self.config.household_name} grocery list",
            shopping_line,
            f"Area: {self.config.area} within {self.config.radius_miles} miles",
            f"Favorite stores: {stores}",
            "Items:",
        ]
        if not groups:
            lines.append("- No needed items yet")
        else:
            for category in sorted(groups):
                lines.append(f"- {category}: {', '.join(groups[category])}")
        return "\n".join(lines)

    def find_matching_deals(self, raw_deals: Iterable[Mapping[str, object]]) -> list[Deal]:
        needed = {item.name for item in self.list_needed_items()}
        matched: list[Deal] = []
        for raw in raw_deals:
            item_name = _normalize_name(str(raw["item"]))
            if item_name not in needed:
                continue
            deal = Deal(
                store=str(raw["store"]),
                item=item_name,
                price=float(raw["price"]),
                original_price=float(raw["original_price"]),
                distance_miles=float(raw.get("distance_miles", 0.0)),
            )
            if deal.distance_miles <= self.config.radius_miles:
                matched.append(deal)
        return sorted(matched, key=lambda deal: (-deal.savings, deal.distance_miles, deal.price))

    def export_confirmed_note(self) -> str:
        lines = ["# Grocery List", ""]
        confirmed = [item for item in self.items if item.status == "confirmed"]
        if not confirmed:
            lines.append("No confirmed grocery items yet.")
        else:
            for item in confirmed:
                quantity = f" ({item.quantity})" if item.quantity else ""
                lines.append(f"- {item.name}{quantity}")
        return "\n".join(lines)


def _parse_request(text: str) -> tuple[str | None, str]:
    cleaned = text.strip().lower()
    if cleaned.startswith("add "):
        cleaned = cleaned[4:].strip()
    parts = cleaned.split()
    if len(parts) >= 3 and parts[0].isdigit():
        name_parts = parts[2:]
        if name_parts and name_parts[0] == "of":
            name_parts = name_parts[1:]
        return " ".join(parts[:2]), " ".join(name_parts)
    return None, _normalize_name(cleaned)


def _normalize_name(text: str) -> str:
    return text.strip().lower()


def _categorize(name: str) -> str:
    words = set(name.split())
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if words & keywords or name in keywords:
            return category
    return "other"
