import json
import os
import subprocess
import sys
from pathlib import Path

from grocery_agent.cli import run
from grocery_agent.storage import JsonStore


def _run_cli(state: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "grocery_agent.cli", "--state", str(state), *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_cli_setup_creates_household_config(tmp_path: Path, capsys):
    state = tmp_path / "state.json"

    exit_code = run([
        "--state", str(state),
        "setup",
        "--name", "Farm House",
        "--area", "90210",
        "--radius", "12",
        "--shopping-days", "saturday,wednesday",
        "--stores", "Kroger,Costco",
    ])

    assert exit_code == 0
    loaded = JsonStore(state).load()
    assert loaded.config.household_name == "Farm House"
    assert loaded.config.shopping_days == ["saturday", "wednesday"]
    assert loaded.config.favorite_stores == ["Kroger", "Costco"]
    assert "Saved setup for Farm House" in capsys.readouterr().out


def test_cli_add_and_digest_persist_items(tmp_path: Path, capsys):
    state = tmp_path / "state.json"
    run(["--state", str(state), "setup", "--name", "House", "--area", "10001"])

    add_code = run(["--state", str(state), "add", "milk", "--by", "Farmer"])
    digest_code = run(["--state", str(state), "digest"])

    output = capsys.readouterr().out
    assert add_code == 0
    assert digest_code == 0
    assert "Added milk" in output
    assert "House grocery list" in output
    assert "Dairy: milk" in output


def test_cli_adds_unique_item_ids_across_separate_processes(tmp_path: Path):
    state = tmp_path / "state.json"

    setup = _run_cli(state, "setup", "--name", "House", "--area", "10001")
    first_add = _run_cli(state, "add", "milk", "--by", "A")
    second_add = _run_cli(state, "add", "eggs", "--by", "B")

    assert setup.returncode == 0, setup.stderr
    assert first_add.returncode == 0, first_add.stderr
    assert second_add.returncode == 0, second_add.stderr
    data = json.loads(state.read_text())
    ids = [item["id"] for item in data["items"]]
    assert ids == ["item_1", "item_2"]


def test_cli_confirm_then_export_note_persists_confirmed_item(tmp_path: Path):
    state = tmp_path / "state.json"

    assert _run_cli(state, "setup", "--name", "House", "--area", "10001").returncode == 0
    assert _run_cli(state, "add", "milk", "--by", "Farmer").returncode == 0
    confirm = _run_cli(state, "confirm", "milk")
    exported = _run_cli(state, "export-note")

    assert confirm.returncode == 0, confirm.stderr
    assert "Confirmed milk" in confirm.stdout
    assert exported.returncode == 0, exported.stderr
    assert "- milk" in exported.stdout
    assert "No confirmed grocery items yet." not in exported.stdout


def test_cli_deals_reports_matching_deals_from_json_file(tmp_path: Path, capsys):
    state = tmp_path / "state.json"
    deals = tmp_path / "deals.json"
    deals.write_text('[{"store":"Kroger","item":"milk","price":3.0,"original_price":5.0,"distance_miles":2}]')
    run(["--state", str(state), "setup", "--name", "House", "--area", "10001"])
    run(["--state", str(state), "add", "milk", "--by", "Farmer"])

    exit_code = run(["--state", str(state), "deals", "--deals-file", str(deals)])

    assert exit_code == 0
    assert "Kroger: milk $3.00 (save $2.00, 2.0 mi)" in capsys.readouterr().out
