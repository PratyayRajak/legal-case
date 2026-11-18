"""Rule YAML loader and registry."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from rules.models import Rule, RuleResult, RuleStatus


def load_rules(directory: Path | None = None) -> list[Rule]:
    """Load all YAML rule files from the rules directory."""
    if directory is None:
        directory = Path(__file__).parent / "definitions"

    rules: list[Rule] = []
    if not directory.exists():
        return rules

    for yaml_file in sorted(directory.glob("*.yaml")):
        rules.extend(load_rules_from_file(yaml_file))
    return rules


def load_rules_from_file(file_path: str | Path) -> list[Rule]:
    """Load rules from a specific YAML file."""
    p = Path(file_path)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    rules: list[Rule] = []
    if isinstance(data, list):
        for item in data:
            rules.append(Rule(**item))
    elif isinstance(data, dict):
        rules.append(Rule(**data))
    return rules


def active_rules(directory: Path | None = None) -> list[Rule]:
    """Return only ACTIVE rules (safe for production use)."""
    return [r for r in load_rules(directory) if r.status == RuleStatus.ACTIVE]


# Registry of check functions: rule_id -> Callable
CheckFunction = Callable[[dict[str, Any]], RuleResult]
_registry: dict[str, CheckFunction] = {}


def register_check(rule_id: str) -> Callable[[CheckFunction], CheckFunction]:
    """Decorator to register a check function for a rule."""

    def decorator(func: CheckFunction) -> CheckFunction:
        _registry[rule_id] = func
        return func

    return decorator


def get_check(rule_id: str) -> CheckFunction | None:
    return _registry.get(rule_id)
