"""Explicit publisher registry. Add one line per new publisher."""

from datafactory.core.errors import PluginNotFoundError
from datafactory.publish.base import Publisher
from datafactory.publish.publishers.local_folder import LocalFolderPublisher

PUBLISHERS: dict[str, type[Publisher]] = {
    LocalFolderPublisher.name: LocalFolderPublisher,
}


def get_publisher(name: str) -> Publisher:
    try:
        return PUBLISHERS[name]()
    except KeyError:
        raise PluginNotFoundError(f"unknown publisher {name!r}") from None
