# Grocery Agent Architecture

## Goal

Build a reusable, self-hostable grocery agent that starts with shared grocery lists and local deal discovery, then grows into recipes, local activities, and carefully approved commerce flows.

## Current MVP modules

- `grocery_agent.core`
  - `HouseholdConfig`
  - `GroceryItem`
  - `Deal`
  - `GroceryAgent`
  - normalization, categorization, digest, deal matching, confirmed-note export
- `grocery_agent.storage`
  - JSON persistence for local-first state
- `grocery_agent.imessage`
  - BlueBubbles webhook payload normalization
  - iMessage-style chat commands (`add`, `remove`, `confirm`, `what do we need?`)
  - grocery-specific message handling that can sit behind Hermes Gateway

## Adapter boundaries to add next

### Messaging adapters

The preferred MVP transport is iMessage through Hermes Gateway + BlueBubbles. `grocery_agent.imessage` now contains the grocery-specific command handler; Hermes should continue to own BlueBubbles auth, webhook registration, session routing, delivery, and media handling.

Target platforms:

- iMessage through BlueBubbles via Hermes Gateway
- Telegram
- Discord
- WhatsApp/SMS
- Slack

Expected interface:

```python
class MessagingAdapter:
    def send_message(self, channel_id: str, text: str) -> None: ...
    def receive_events(self) -> Iterable[MessageEvent]: ...
```

### List backends

Target backends:

- JSON/SQLite canonical local state
- Markdown shared-note export
- Apple Reminders/CalDAV if viable
- Apple Notes through Shortcuts/macOS automation if viable
- Notion/Google Sheets later

### Deal sources

Target sources:

- manually supplied JSON feed first
- store weekly ad adapters
- Kroger/Walmart/Target public/API adapters where available
- browser-based fallback if allowed by site terms

### Scheduler

Target jobs:

- daily deal scan
- shopping-day reminder
- weekly recipe suggestion
- weekly activity/date-night suggestion

Hermes cron can run these jobs when deployed as a Hermes profile/plugin. A standalone worker can also run them from cron/systemd/container schedules.

## Safety model

- Read/list actions may be automatic.
- Shared-list writes require confirmation until household trust settings are added.
- Purchase/cart actions are future work only.
- Any AgentCash/Instacart flow must include spend limits, explicit confirmation, receipt logging, and cancellation/refund handling.
