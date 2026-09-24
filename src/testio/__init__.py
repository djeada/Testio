"""Testio: run programs against expected-output test suites."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("testio")
except PackageNotFoundError:  # running from a source tree without installing
    __version__ = "0.0.0+unknown"
