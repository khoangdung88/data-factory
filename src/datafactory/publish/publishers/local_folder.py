"""Copy the package to a local folder (default ``<data_dir>/exports/<slug>-<version>/``)."""

import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from datafactory.publish.base import PublishContext, Publisher


class LocalFolderParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_dir: str = "exports"


class LocalFolderPublisher(Publisher):
    name = "local_folder"
    version = "1.0.0"

    def publish(self, ctx: PublishContext, params: Mapping[str, Any]) -> str:
        p = LocalFolderParams.model_validate(params)
        root = Path(p.target_dir)
        if not root.is_absolute():
            root = ctx.settings.data_dir / root
        dest = root / f"{ctx.package.name}-{ctx.package.version}"
        shutil.copytree(ctx.package_dir, dest, dirs_exist_ok=True)
        return str(dest)
