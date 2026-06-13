import subprocess
import sys
from pathlib import Path


def test_module_entrypoint_invokes_cli(tmp_path: Path):
    state = tmp_path / "state.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "grocery_agent.cli",
            "--state",
            str(state),
            "setup",
            "--name",
            "Farm House",
            "--area",
            "90210",
        ],
        cwd=Path(__file__).parents[1],
        env={"PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Saved setup for Farm House" in result.stdout
    assert state.exists()
