# Apple Notes Shared Grocery List

The grocery agent should be able to work with a shared Apple Notes note, but it should not pretend Apple Notes has a normal public server API.

## Reality check

Apple Notes/iCloud Notes does not provide a reliable public cross-platform API for third-party apps to create shared notes and invite collaborators. For safety and portability, this repo now supports a staged Apple Notes flow:

1. Grocery Agent generates a deterministic note draft from confirmed grocery items.
2. Grocery Agent tracks the people you want invited in household setup.
3. Grocery Agent creates an invite handoff/plan that either:
   - you follow manually in Apple Notes, or
   - a trusted macOS/iOS Shortcuts or AppleScript bridge executes later.

This means the app can help create/update the Apple Notes content and tell you exactly who to invite now, while leaving fully automatic invites as a future macOS/iOS automation integration.

## Configure invitees

```bash
python -m grocery_agent.cli --state ./state.json setup \
  --name "Farm House" \
  --area "90210" \
  --note-invitees "farmer@icloud.com,+155****4567"
```

The same `note_invitees` field can later be filled from onboarding UI or iMessage setup prompts.

## Generate the Apple Notes invite plan

```bash
python -m grocery_agent.cli --state ./state.json apple-note-plan
```

The output includes:

- Apple Notes title
- grocery note body from confirmed items
- limitation/safety note
- manual invite steps
- invitee list

## iMessage command

In the iMessage group chat, after Hermes/BlueBubbles is wired in, users can ask:

```text
@grocery share note
```

The handler responds with:

- the Apple Notes draft title
- the confirmed grocery list body
- configured invitees
- the next manual step: open Apple Notes and use Share Note > Collaborate

## Future automation bridge

`AppleNotesSyncPlanner.build_shortcuts_payload()` returns a stable payload for a future macOS/iOS bridge:

```json
{
  "action": "create_or_update_shared_apple_note",
  "title": "Farm House Grocery List",
  "body": "# Grocery List\n\n- milk",
  "invitees": ["farmer@icloud.com"]
}
```

A future bridge can receive this payload and use Shortcuts/AppleScript/UI automation on a Mac signed into iCloud to create or update the note. Any automatic invite flow should still require explicit household approval until permissions are mature.

## Manual Apple Notes invite steps

1. Open Notes on the Mac/iPhone signed into iCloud.
2. Create or open the generated note title.
3. Paste/update the grocery list content.
4. Tap/click Share Note.
5. Choose Collaborate, not Send Copy.
6. Invite only the configured people.
7. Confirm back in the grocery chat once the note and invites are ready.
