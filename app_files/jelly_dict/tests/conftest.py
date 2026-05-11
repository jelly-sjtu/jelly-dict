from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch, tmp_path: Path) -> Iterator[Path]:
    """Redirect runtime data (settings, cache, logs) to a tmp dir per test."""
    monkeypatch.setenv("JELLY_DICT_HOME", str(tmp_path))
    yield tmp_path
