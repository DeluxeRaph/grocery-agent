# iMessage / BlueBubbles Integration

The product chat should live in iMessage, not the CLI. The CLI remains useful for local setup, smoke tests, and development, but the household-facing interface should be an iMessage group chat.

Hermes Gateway supports BlueBubbles (iMessage), so the recommended path is:

```text
iMessage group chat
  -> Messages.app on an always-on Mac
  -> BlueBubbles Server webhook
  -> Hermes Gateway
  -> Grocery Agent message handler
  -> BlueBubbles REST API reply
  -> iMessage group chat
```

## Prerequisites

- An always-on Mac running BlueBubbles Server
- Apple ID signed into Messages.app on that Mac
- BlueBubbles Server v1.0.0 or newer
- Network connectivity between the Hermes host and the BlueBubbles Server
- Hermes Gateway configured with a model provider

## Configure Hermes BlueBubbles

Interactive setup:

```bash
hermes gateway setup
```

Choose `BlueBubbles (iMessage)` and enter the BlueBubbles server URL/password.

Manual environment setup in `~/.hermes/.env`:

```bash
BLUEBUBBLES_SERVER_URL=http://192.168.1.10:1234
BLUEBUBBLES_PASSWORD=your-server-password
```

Optional authorization controls:

```bash
# Pre-authorize selected iMessage users
BLUEBUBBLES_ALLOWED_USERS=user@icloud.com,+15551234567

# Or allow all users during local prototyping only
BLUEBUBBLES_ALLOW_ALL_USERS=true
```

For group chats, prefer mention-gating until household permissions are more mature:

```yaml
platforms:
  bluebubbles:
    enabled: true
    extra:
      require_mention: true
      mention_patterns:
        - '(?<![\w@])@?grocery\b[,:\-]?'
```

Then start Hermes Gateway:

```bash
hermes gateway run
```

Hermes registers the BlueBubbles webhook and can receive/send iMessages.

## Grocery message behavior added in this repo

`src/grocery_agent/imessage.py` adds a tested grocery-specific handler for iMessage messages:

- `add eggs` -> adds eggs to the list with the iMessage sender as requester
- `remove bananas` -> marks bananas removed while keeping history
- `confirm milk` -> marks milk confirmed for shared-note export
- `what do we need?` / `list` -> returns the current grocery digest
- unknown messages -> returns short help text without mutating state

The handler is transport-light on purpose. Hermes/BlueBubbles should own the live iMessage transport, auth, sessions, typing indicators, media, and delivery. Grocery Agent owns the domain behavior.

## Programmatic handler example

```python
from grocery_agent.imessage import BlueBubblesEvent, GroceryMessageHandler
from grocery_agent.storage import JsonStore

handler = GroceryMessageHandler(JsonStore("./state.json"))
reply = handler.handle(
    BlueBubblesEvent(
        chat_id="iMessage;+;chat-guid",
        sender="+15551234567",
        text="add eggs",
    )
)
# reply: "Added eggs to the grocery list."
```

## Webhook payload normalization

`parse_bluebubbles_webhook(payload)` normalizes BlueBubbles webhook payloads into `BlueBubblesEvent` and ignores messages sent by the Mac/agent itself to prevent reply loops.

This gives us a small, testable seam that can be wired into either:

1. a Hermes Gateway platform hook/plugin, or
2. a standalone web server that receives BlueBubbles webhooks and calls the BlueBubbles REST API.

The Hermes route is preferred because Hermes already handles BlueBubbles setup, authorization, group chat delivery, media, model/provider selection, cron jobs, and future agent tools.
