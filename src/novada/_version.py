"""Single source of truth for the package version."""

from __future__ import annotations

# __version__ is read both at runtime (exported from novada) and at build time
# (hatchling reads it via [tool.hatch.version]). It is also sent as part of the
# default User-Agent header on every request.
__version__ = "0.1.0"
