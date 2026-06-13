from pathlib import Path

from grocery_agent.cli import run
from grocery_agent.storage import JsonStore


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


def test_cli_deals_reports_matching_deals_from_json_file(tmp_path: Path, capsys):
    state = tmp_path / "state.json"
    deals = tmp_path / "deals.json"
    deals.write_text('[{"store":"Kroger","item":"milk","price":3.0,"original_price":5.0,"distance_miles":2}]')
    run(["--state", str(state), "setup", "--name", "House", "--area", "10001"])
    run(["--state", str(state), "add", "milk", "--by", "Farmer"])

    exit_code = run(["--state", str(state), "deals", "--deals-file", str(deals)])

    assert exit_code == 0
    assert "Kroger: milk $3.00 (save $2.00, 2.0 mi)" in capsys.readouterr().out
