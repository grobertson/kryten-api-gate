"""kryten-api-gate: HTTP REST gateway for the Kryten ecosystem."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("kryten-api-gate")
except PackageNotFoundError:
    __version__ = "0.0.0"
