from __future__ import annotations

import json
import os
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Iterator, TypeVar

import fcntl

from grocery_agent.core import GroceryAgent, GroceryItem, HouseholdConfig

T = TypeVar("T")
_PATH_LOCKS: dict[Path, threading.RLock] = {}
_PATH_LOCKS_GUARD = threading.Lock()


class JsonStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock_path = self.path.with_name(f"{self.path.name}.lock")
        self._thread_lock = _thread_lock_for(self.path)

    def load(self, default_area: str = "00000") -> GroceryAgent:
        with self._locked():
            return self._load_unlocked(default_area=default_area)

    def save(self, agent: GroceryAgent) -> None:
        with self._locked():
            self._save_unlocked(agent)

    def update(self, mutator: Callable[[GroceryAgent], T], default_area: str = "00000") -> T:
        """Serialize a load/mutate/save transaction against this JSON state file."""

        with self._locked():
            agent = self._load_unlocked(default_area=default_area)
            result = mutator(agent)
            self._save_unlocked(agent)
            return result

    def _load_unlocked(self, default_area: str = "00000") -> GroceryAgent:
        if not self.path.exists():
            return GroceryAgent.default_for(area=default_area)

        data = json.loads(self.path.read_text())
        config = HouseholdConfig(**data["config"])
        items = [GroceryItem(**item) for item in data.get("items", [])]
        agent = GroceryAgent(config=config, next_item_number=data.get("next_item_id", _next_item_number(items)))
        agent.items = items
        return agent

    def _save_unlocked(self, agent: GroceryAgent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "config": asdict(agent.config),
            "items": [asdict(item) for item in agent.items],
            "next_item_id": agent._next_item_number,
        }
        payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile("w", dir=self.path.parent, prefix=f".{self.path.name}.", suffix=".tmp", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(payload)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_path, self.path)
        finally:
            if temp_path is not None and os.path.exists(temp_path):
                os.unlink(temp_path)

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._thread_lock:
            with self._lock_path.open("a") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _thread_lock_for(path: Path) -> threading.RLock:
    resolved = path.resolve()
    with _PATH_LOCKS_GUARD:
        lock = _PATH_LOCKS.get(resolved)
        if lock is None:
            lock = threading.RLock()
            _PATH_LOCKS[resolved] = lock
        return lock


def _next_item_number(items: list[GroceryItem]) -> int:
    numbers: list[int] = []
    for item in items:
        prefix, _, suffix = item.id.partition("_")
        if prefix == "item" and suffix.isdigit():
            numbers.append(int(suffix))
    return max(numbers, default=0) + 1
