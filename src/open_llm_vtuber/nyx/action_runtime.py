from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .audit import AuditLog
from .security import NyxSecurityGuard, PermissionDeniedError, SecurityPolicy


@dataclass
class AllowedAction:
    name: str
    description: str
    handler: Any
    allow_write: bool = False
    allow_shell: bool = False


@dataclass
class LocalActionRuntime:
    """Action runtime aligned with the Nyx governance model."""

    allowed_roots: List[str] = field(default_factory=lambda: ["."])
    audit: AuditLog = field(default_factory=AuditLog)
    guard: NyxSecurityGuard = field(default_factory=NyxSecurityGuard)
    actions: Dict[str, AllowedAction] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.guard = NyxSecurityGuard(SecurityPolicy(allowed_roots=self.allowed_roots))

    def register(self, action: AllowedAction) -> None:
        self.actions[action.name] = action

    def read_text(self, target: str) -> str:
        self.guard.validate_target(target, "read_text")
        self.audit.record("read_text", {"target": target})
        return Path(target).read_text(encoding="utf-8")

    def write_text(self, target: str, content: str) -> str:
        self.guard.validate_target(target, "write_text")
        target_path = Path(target)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        self.audit.record("write_text", {"target": target, "length": len(content)})
        return str(target_path)

    def run_shell(self, command: str) -> str:
        import subprocess

        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout.strip() or result.stderr.strip() or ""
        self.audit.record("run_shell", {"command": command, "output": output[:200]})
        return output

    def run(self, action_name: str, **kwargs: Any) -> Any:
        action = self.actions.get(action_name)
        if action is None:
            raise KeyError(f"Unknown action '{action_name}'")

        if "target" in kwargs and not action.allow_write and not action.allow_shell:
            self.guard.validate_target(str(kwargs["target"]), action_name)

        if action.allow_shell:
            return action.handler(**kwargs)
        if action.allow_write:
            return action.handler(**kwargs)
        return action.handler(**kwargs)
