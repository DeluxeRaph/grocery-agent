# Grocery Agent

A self-hostable grocery and household coordination agent MVP for singles, couples, roommates, families, and community houses.

The first milestone focuses on a practical grocery loop:

- household setup with area/ZIP, travel radius, shopping days, favorite stores, budget mode, and dietary preferences
- grocery requests from an iMessage group chat through Hermes + BlueBubbles
- normalized grocery items with categories and requester tracking
- daily deal matching against a deal feed/adapter input
- shopping-day digest generation
- confirmed-item export as markdown for a shared note/list backend

Future modules will add Apple Notes/Reminders sync, recipes, local activities, Instacart/cart integrations, and AgentCash-powered purchase experiments.

## MVP status

This repo currently ships a tested core library, local CLI, and iMessage/BlueBubbles message handler. The CLI is mainly for setup, smoke tests, and local development; the household-facing chat experience should run through Hermes Gateway's BlueBubbles/iMessage support.

## Quick start

```bash
cd grocery-agent
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'

# Create household setup
python -m grocery_agent.cli --state ./state.json setup \
  --name "Farm House" \
  --area "90210" \
  --radius 10 \
  --shopping-days "saturday,wednesday" \
  --stores "Kroger,Costco,Target"

# Add grocery requests
python -m grocery_agent.cli --state ./state.json add "2 gallons of whole milk" --by Farmer
python -m grocery_agent.cli --state ./state.json add "eggs" --by Cloud

# Print shopping digest
python -m grocery_agent.cli --state ./state.json digest
```

## iMessage group chat setup

Hermes can already connect to iMessage through BlueBubbles. See `docs/imessage.md` for the live-chat path. The short version:

1. Run BlueBubbles Server on an always-on Mac signed into Messages.app.
2. Configure Hermes Gateway with `hermes gateway setup` and choose `BlueBubbles (iMessage)`.
3. Set `BLUEBUBBLES_SERVER_URL` and `BLUEBUBBLES_PASSWORD` in `~/.hermes/.env` if configuring manually.
4. Run `hermes gateway run` or install/start the gateway service.
5. Use this project's `GroceryMessageHandler` as the grocery-specific handler for messages like `add eggs`, `remove bananas`, `confirm milk`, `what do we need?`, and `share note`.

## Deal matching input

For the MVP, deal sources are adapter-shaped JSON. Store scrapers/APIs can later produce this same shape.

```json
[
  {
    "store": "Kroger",
    "item": "milk",
    "price": 3.0,
    "original_price": 5.0,
    "distance_miles": 2
  }
]
```

Run:

```bash
python -m grocery_agent.cli --state ./state.json deals --deals-file ./deals.json
```

## Shared note export

Confirmed grocery items can be exported as markdown. Confirm a needed item by id (for example `item_1`) or normalized name before exporting:

```bash
python -m grocery_agent.cli --state ./state.json confirm "whole milk"
python -m grocery_agent.cli --state ./state.json export-note
```

Apple Notes has no simple public API, so the MVP treats markdown/JSON as the canonical source of truth. The repo now includes an Apple Notes planner for generating a shared-note draft, configured invitee list, manual invite steps, and a stable Shortcuts/AppleScript handoff payload. See `docs/apple-notes.md`.

## Design principles

- Modular adapters over one hardcoded app path
- Local-first state by default
- Any model provider: local or cloud
- Explicit confirmation before shared-list writes or purchases
- No real purchase actions in the MVP
- Clear audit trail via persisted state
- Single-person, couple, roommate, family, and community-house use cases

## Test

```bash
python3 -m pytest
```
