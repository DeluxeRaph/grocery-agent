from __future__ import annotations

import argparse
import json
from pathlib import Path

from grocery_agent.core import GroceryAgent, HouseholdConfig
from grocery_agent.storage import JsonStore

DEFAULT_STATE = Path.home() / ".grocery-agent" / "state.json"


def run(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    store = JsonStore(args.state)

    if args.command == "setup":
        agent = GroceryAgent(
            config=HouseholdConfig(
                household_name=args.name,
                area=args.area,
                radius_miles=args.radius,
                shopping_days=_csv(args.shopping_days),
                favorite_stores=_csv(args.stores),
                budget_mode=args.budget_mode,
                dietary_preferences=_csv(args.dietary_preferences),
            )
        )
        store.save(agent)
        print(f"Saved setup for {agent.config.household_name}")
        return 0

    agent = store.load()

    if args.command == "add":
        item = agent.add_request(args.text, requested_by=args.by)
        store.save(agent)
        print(f"Added {item.name}")
        return 0

    if args.command == "remove":
        removed = agent.remove_item(args.name)
        store.save(agent)
        print(f"Removed {args.name}" if removed else f"No needed item named {args.name}")
        return 0 if removed else 1

    if args.command == "confirm":
        confirmed = agent.confirm_item(args.item)
        store.save(agent)
        print(f"Confirmed {args.item}" if confirmed else f"No needed item matching {args.item}")
        return 0 if confirmed else 1

    if args.command == "digest":
        print(agent.build_grocery_digest())
        return 0

    if args.command == "deals":
        raw_deals = json.loads(Path(args.deals_file).read_text())
        deals = agent.find_matching_deals(raw_deals)
        if not deals:
            print("No matching deals found for the current list.")
        for deal in deals:
            print(f"{deal.store}: {deal.item} ${deal.price:.2f} (save ${deal.savings:.2f}, {deal.distance_miles:.1f} mi)")
        return 0

    if args.command == "export-note":
        print(agent.export_confirmed_note())
        return 0

    parser.print_help()
    return 1


def main() -> None:
    raise SystemExit(run())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grocery Agent MVP")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE, help="Path to JSON state file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser("setup", help="Create household grocery-agent config")
    setup.add_argument("--name", required=True)
    setup.add_argument("--area", required=True, help="ZIP code or city/area")
    setup.add_argument("--radius", type=int, default=10)
    setup.add_argument("--shopping-days", default="saturday")
    setup.add_argument("--stores", default="")
    setup.add_argument("--budget-mode", default="balanced")
    setup.add_argument("--dietary-preferences", default="")

    add = subparsers.add_parser("add", help="Add a grocery request")
    add.add_argument("text")
    add.add_argument("--by", required=True)

    remove = subparsers.add_parser("remove", help="Remove a needed item")
    remove.add_argument("name")

    confirm = subparsers.add_parser("confirm", help="Confirm a needed item by id or name for shared-note export")
    confirm.add_argument("item")

    subparsers.add_parser("digest", help="Print grocery digest")

    deals = subparsers.add_parser("deals", help="Match current list against a JSON deals file")
    deals.add_argument("--deals-file", required=True)

    subparsers.add_parser("export-note", help="Export confirmed items as shared-note markdown")
    return parser


def _csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


if __name__ == "__main__":
    main()
