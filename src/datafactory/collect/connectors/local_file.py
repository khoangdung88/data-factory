"""Copy a local file (absolute or relative to the dataset folder) into the raw zone."""

import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from datafactory.collect.base import Connector, FetchContext
from datafactory.core.errors import ConfigError


class LocalFileParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str


class LocalFileConnector(Connector):
    name = "local_file"
    version = "1.0.0"

    def fetch(self, params: Mapping[str, Any], ctx: FetchContext) -> str:
        p = LocalFileParams.model_validate(params)
        src = Path(p.path)
        if not src.is_absolute():
            src = ctx.dataset_dir / src
        if not src.is_file():
            raise ConfigError(f"local_file: {p.path} not found")
        shutil.copyfile(src, ctx.dest / src.name)
        return p.path
