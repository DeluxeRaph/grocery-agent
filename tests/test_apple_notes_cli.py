from pathlib import Path

from grocery_agent.cli import run
from grocery_agent.storage import JsonStore


def test_cli_setup_stores_apple_notes_invitees(tmp_path: Path):
    state = tmp_path / "state.json"

    exit_code = run([
        "--state", str(state),
        "setup",
        "--name", "Farm House",
        "--area", "90210",
        "--note-invitees", "farmer@icloud.com,+155****4567",
    ])

    assert exit_code == 0
    assert JsonStore(state).load().config.note_invitees == ["farmer@icloud.com", "+155****4567"]


def test_cli_apple_note_plan_prints_manual_invite_steps(tmp_path: Path, capsys):
    state = tmp_path / "state.json"
    run(["--state", str(state), "setup", "--name", "Farm House", "--area", "90210", "--note-invitees", "farmer@icloud.com"])
    run(["--state", str(state), "add", "milk", "--by", "Farmer"])
    run(["--state", str(state), "confirm", "milk"])

    exit_code = run(["--state", str(state), "apple-note-plan"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Farm House Grocery List" in output
    assert "Apple Notes has no public cross-platform invite API" in output
    assert "Invite these people: farmer@icloud.com" in output
    assert "- milk" in output
