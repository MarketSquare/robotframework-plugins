"""Custom exception hierarchy for the evaluation harness."""

from __future__ import annotations


class RfSkillEvalError(Exception):
    """Base class for all harness-specific errors."""


class AuthConfigError(RfSkillEvalError):
    """Raised when no usable Claude authentication is available."""


class ModelNotAllowedError(RfSkillEvalError, ValueError):
    """Raised when a task or CLI requests a forbidden model (e.g., Opus)."""


class RunnerTimeout(RfSkillEvalError):
    """Raised when the Claude CLI subprocess exceeds its wall-clock budget."""


class SkillRunnerError(RfSkillEvalError):
    """Raised for generic failures while invoking the skill runner."""


class GraderError(RfSkillEvalError):
    """Raised when the deterministic grader fails to execute."""
