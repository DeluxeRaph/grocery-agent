# Grocery Agent MVP Product Notes

## Primary user stories

- As a single person, I can keep a grocery list through the messaging app I already use.
- As a couple, roommate group, family, or community house, multiple people can request groceries in a shared channel.
- As a shopper, I get a digest before shopping day with the current list and relevant deals.
- As a privacy-conscious user, I can run the app locally and choose my own model provider.

## MVP acceptance criteria

- A household can be configured with area, radius, stores, and shopping days.
- A grocery request can be added with requester tracking.
- Items are normalized and grouped by category.
- Removed items stay in history.
- Deal candidates are matched only against current needed items.
- Deals are ranked by savings, then distance.
- Confirmed items export to a shared-note-friendly markdown format.
- The project has tests for core behavior, persistence, and CLI flows.

## Out of scope for MVP

- Real purchases
- Instacart checkout
- AgentCash payment execution
- Apple Notes write automation
- Full natural-language conversation memory
- Multi-household hosted SaaS auth
