"""robotframework-plugins — cross-agent installer for Robot Framework agent plugins.

The package bundles the plugin tree (skills, subagents, hooks, scripts)
inside ``robotframework_plugins/_assets/`` and provides per-agent adapters that
copy / transform that tree into each target's expected install paths.

See ``docs/installer/proposal.md`` (in the source repo) for the full
design and compatibility matrix.
"""

from __future__ import annotations

__version__ = "2026.11.0"
__all__ = ("__version__",)
