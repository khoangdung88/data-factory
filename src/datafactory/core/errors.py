"""Typed errors. Every expected failure raises a ``DataFactoryError`` subclass."""


class DataFactoryError(Exception):
    """Base class for all expected data-factory errors."""


class ConfigError(DataFactoryError):
    """Invalid dataset definition or plugin parameters."""


class PluginNotFoundError(DataFactoryError):
    """No plugin registered under the requested name."""


class BatchNotFoundError(DataFactoryError):
    """A required batch is missing from a data zone."""


class CollectError(DataFactoryError):
    """A connector failed to produce raw data."""


class QualityGateError(DataFactoryError):
    """Processed data does not meet the dataset's quality gates."""


class ProductExistsError(DataFactoryError):
    """A product version already exists with different content."""
