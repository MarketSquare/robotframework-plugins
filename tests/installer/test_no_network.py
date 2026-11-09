"""A file-mode install makes no network call (spec adoption-reporting, "No
telemetry"; launch task 8.3). Sockets are blocked in the test process, so any
connection attempt, by the installer or a library it imports, fails the test."""
from __future__ import annotations

import socket
from pathlib import Path

import pytest

from robotframework_plugins.cli import main

AGENTS = ("claude-code", "copilot", "codex", "cursor", "goose", "opencode", "claude-desktop")


class NetworkCall(AssertionError):
    pass


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    attempts: list[str] = []

    def refuse(*args, **kwargs):
        attempts.append(repr(args[:2]))
        raise NetworkCall(f"network call during install: {args[:2]!r}")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    return attempts


@pytest.mark.parametrize("agent", AGENTS)
def test_file_mode_install_makes_no_network_call(agent: str, no_network: list[str], fake_home: Path,
                                                 tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    (project / "pyproject.toml").write_text('[project]\nname = "p"\ndependencies = ["robotframework-browser"]\n')
    rc = main(["install", "--agent", agent, "--scope", "project", "--project", str(project), "--yes"])
    assert rc == 0
    assert no_network == []


def test_the_guard_works(no_network: list[str]) -> None:
    with pytest.raises(NetworkCall):
        socket.create_connection(("pypi.org", 443))
    assert no_network
