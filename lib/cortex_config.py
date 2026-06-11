#!/usr/bin/env python3
"""Load Cortex project config with optional local overrides.

This intentionally supports the small YAML subset emitted by cortex-setup:
top-level maps, nested maps, lists of scalars, strings, and comments.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


class ConfigError(RuntimeError):
    pass


def _strip_comment(line: str) -> str:
    in_quote: str | None = None
    escaped = False
    output: list[str] = []

    for char in line:
        if escaped:
            output.append(char)
            escaped = False
            continue
        if char == "\\" and in_quote == '"':
            output.append(char)
            escaped = True
            continue
        if char in ("'", '"'):
            if in_quote is None:
                in_quote = char
            elif in_quote == char:
                in_quote = None
            output.append(char)
            continue
        if char == "#" and in_quote is None:
            break
        output.append(char)

    if in_quote is not None:
        raise ConfigError("unterminated quoted string")
    return "".join(output).rstrip()


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    if value in ("[]", "{}"):
        return [] if value == "[]" else {}
    return value


def _parse_yaml_subset(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, result)]
    pending_key: tuple[int, dict[str, Any], str] | None = None
    child_indents: dict[int, int] = {}

    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigError(str(exc)) from exc

    for line_number, raw_line in enumerate(raw_lines, start=1):
        try:
            line = _strip_comment(raw_line)
        except ConfigError as exc:
            raise ConfigError(f"{path}:{line_number}: {exc}") from exc

        if not line.strip():
            continue
        leading_whitespace = raw_line[: len(raw_line) - len(raw_line.lstrip())]
        if "\t" in leading_whitespace:
            raise ConfigError(f"{path}:{line_number}: tabs are not supported")

        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ConfigError(f"{path}:{line_number}: invalid indentation")

        parent = stack[-1][1]

        if pending_key is not None and indent > pending_key[0]:
            pending_indent, pending_parent, key = pending_key
            if text.startswith("- "):
                container: Any = []
            else:
                container = {}
            pending_parent[key] = container
            stack.append((pending_indent, container))
            parent = container
            pending_key = None
        elif pending_key is not None:
            pending_key = None

        expected_indent = child_indents.get(id(parent))
        if expected_indent is None:
            child_indents[id(parent)] = indent
        elif indent != expected_indent:
            raise ConfigError(f"{path}:{line_number}: invalid indentation")

        if text.startswith("- "):
            if not isinstance(parent, list):
                raise ConfigError(f"{path}:{line_number}: list item without list parent")
            parent.append(_parse_scalar(text[2:]))
            continue

        if ":" not in text:
            raise ConfigError(f"{path}:{line_number}: expected key/value pair")

        key, value = text.split(":", 1)
        key = key.strip()
        if not key:
            raise ConfigError(f"{path}:{line_number}: empty key")
        if not isinstance(parent, dict):
            raise ConfigError(f"{path}:{line_number}: key/value pair without map parent")

        if value.strip() == "":
            parent[key] = {}
            pending_key = (indent, parent, key)
        else:
            parent[key] = _parse_scalar(value)

    return result


def _merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = _merge(merged.get(key), value)
        return merged
    return override


def load_config(project_dir: Path) -> dict[str, Any]:
    cortex_dir = project_dir / ".cortex"
    base_path = cortex_dir / "config.yaml"
    local_path = cortex_dir / "config.local.yaml"

    if not base_path.exists():
        return {}

    config = _parse_yaml_subset(base_path)
    if local_path.exists():
        config = _merge(config, _parse_yaml_subset(local_path))
    return config


def _get_value(config: dict[str, Any], dotted_key: str) -> Any:
    value: Any = config
    for part in dotted_key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--get", required=True)
    args = parser.parse_args()

    try:
        config = load_config(Path(args.project_dir))
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 2

    value = _get_value(config, args.get)
    if value is None:
        return 1
    if isinstance(value, list):
        print("\n".join(str(item) for item in value))
    elif isinstance(value, dict):
        for key in sorted(value):
            print(f"{key}={value[key]}")
    else:
        print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
