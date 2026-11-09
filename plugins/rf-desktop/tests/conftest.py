"""Plugin tests share the repository test helpers in ``tests/`` (``_shell``, ``_standalone``)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
