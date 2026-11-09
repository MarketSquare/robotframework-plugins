"""rf-agentskills 0.9.0: forwards to robotframework-plugins (spec repository-migration)."""
from __future__ import annotations

import sys

NOTICE = ("rf-agentskills has moved to robotframework-plugins; this command forwards to it. "
          "Use `uvx robotframework-plugins` from now on.")


def main(argv: list[str] | None = None) -> int:
    """Print the notice to stderr, then run robotframework-plugins with the same
    arguments and return its exit code."""
    print(NOTICE, file=sys.stderr)
    from robotframework_plugins.cli import main as forward

    return forward(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    sys.exit(main())
