from datetime import UTC, datetime
from pathlib import Path

import pytest

from datafactory.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = REPO_ROOT / "datasets"
NOW = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "data", datasets_dir=DATASETS_DIR)
