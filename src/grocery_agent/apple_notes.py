from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from grocery_agent.core import GroceryAgent


@dataclass(frozen=True)
class AppleNotesNoteDraft:
    title: str
    body: str
    invitees: list[str]


@dataclass(frozen=True)
class AppleNotesInvitePlan:
    can_auto_invite: bool
    limitation: str
    manual_steps: list[str]
    agent_handoff: dict[str, Any]


class AppleNotesSyncPlanner:
    """Build Apple Notes note/invite payloads without pretending to control iCloud.

    Apple Notes does not expose a reliable public cross-platform API for creating
    shared notes or inviting collaborators. This planner creates deterministic
    drafts and handoff payloads that a macOS Shortcuts/AppleScript bridge or a
    human can use safely.
    """

    def build_note_draft(self, agent: GroceryAgent) -> AppleNotesNoteDraft:
        return AppleNotesNoteDraft(
            title=f"{agent.config.household_name} Grocery List",
            body=agent.export_confirmed_note(),
            invitees=list(agent.config.note_invitees),
        )

    def build_invite_plan(self, draft: AppleNotesNoteDraft) -> AppleNotesInvitePlan:
        invitees = ", ".join(draft.invitees) if draft.invitees else "No invitees configured yet"
        return AppleNotesInvitePlan(
            can_auto_invite=False,
            limitation="Apple Notes has no public cross-platform invite API, so invites require a human or a trusted macOS/iOS automation bridge.",
            manual_steps=[
                "Open Notes on the Mac/iPhone signed into iCloud.",
                f"Create or open a note titled: {draft.title}",
                "Paste/update the grocery list content from the generated note draft.",
                "Tap/click Share Note, choose Collaborate, and keep permissions limited to invited people.",
                f"Invite these people: {invitees}",
                "Confirm in the grocery chat once the shared note is created/invites are sent.",
            ],
            agent_handoff=self.build_shortcuts_payload(draft),
        )

    def build_shortcuts_payload(self, draft: AppleNotesNoteDraft) -> dict[str, Any]:
        return {
            "action": "create_or_update_shared_apple_note",
            "title": draft.title,
            "body": draft.body,
            "invitees": list(draft.invitees),
        }
