import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


NOT_CONFIGURED_VALUES = {"", "NOT_CONFIGURED", "TO_BE_FILLED", "TO_BE_CONFIGURED", "TEMPLATE_ONLY_NOT_RUN"}


def load_structured_config(path: str) -> Dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore

            payload = yaml.safe_load(text)
        except Exception:
            payload = _load_minimal_yaml(text)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"config must be a mapping: {path}")
    return payload


def find_not_configured(payload: Any, prefix: str = "") -> List[str]:
    missing: List[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            missing.extend(find_not_configured(value, child))
    elif isinstance(payload, list):
        for idx, value in enumerate(payload):
            child = f"{prefix}[{idx}]"
            missing.extend(find_not_configured(value, child))
    elif isinstance(payload, str) and payload.strip() in NOT_CONFIGURED_VALUES:
        missing.append(prefix)
    return missing


def resolve_path(value: str, *, base_dir: str = "") -> str:
    if not value or value in NOT_CONFIGURED_VALUES:
        return value
    p = Path(value)
    if p.is_absolute():
        return str(p)
    if base_dir:
        return str((Path(base_dir) / p).resolve())
    return str(p)


def configured(value: Any) -> bool:
    return str(value or "").strip() not in NOT_CONFIGURED_VALUES


def _load_minimal_yaml(text: str) -> Any:
    items = _preprocess_yaml_lines(text)
    if not items:
        return {}
    value, idx = _parse_block(items, 0, items[0][0])
    if idx < len(items):
        raise ValueError(f"could not parse YAML line: {items[idx][1]}")
    return value


def _preprocess_yaml_lines(text: str) -> List[Tuple[int, str]]:
    lines: List[Tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        without_comment = _strip_comment(raw.rstrip())
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        lines.append((indent, without_comment.strip()))
    return lines


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for idx, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:idx].rstrip()
    return line


def _parse_block(items: List[Tuple[int, str]], idx: int, indent: int) -> Tuple[Any, int]:
    if idx >= len(items):
        return {}, idx
    if items[idx][0] < indent:
        return {}, idx
    if items[idx][1].startswith("- "):
        return _parse_list(items, idx, indent)
    return _parse_dict(items, idx, indent)


def _parse_dict(items: List[Tuple[int, str]], idx: int, indent: int) -> Tuple[Dict[str, Any], int]:
    out: Dict[str, Any] = {}
    while idx < len(items):
        cur_indent, text = items[idx]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise ValueError(f"unexpected indentation before: {text}")
        if text.startswith("- "):
            break
        key, value_text = _split_key_value(text)
        idx += 1
        if value_text == "":
            if idx < len(items) and items[idx][0] > cur_indent:
                value, idx = _parse_block(items, idx, items[idx][0])
            else:
                value = {}
        else:
            value = _parse_scalar(value_text)
        out[key] = value
    return out, idx


def _parse_list(items: List[Tuple[int, str]], idx: int, indent: int) -> Tuple[List[Any], int]:
    out: List[Any] = []
    while idx < len(items):
        cur_indent, text = items[idx]
        if cur_indent < indent:
            break
        if cur_indent != indent or not text.startswith("- "):
            break
        item_text = text[2:].strip()
        idx += 1
        if item_text == "":
            if idx < len(items) and items[idx][0] > cur_indent:
                value, idx = _parse_block(items, idx, items[idx][0])
            else:
                value = None
        elif _looks_like_key_value(item_text):
            key, value_text = _split_key_value(item_text)
            value: Dict[str, Any] = {key: _parse_scalar(value_text) if value_text else {}}
            if idx < len(items) and items[idx][0] > cur_indent:
                extra, idx = _parse_block(items, idx, items[idx][0])
                if isinstance(extra, dict):
                    value.update(extra)
            out.append(value)
            continue
        else:
            value = _parse_scalar(item_text)
        out.append(value)
    return out, idx


def _split_key_value(text: str) -> Tuple[str, str]:
    if ":" not in text:
        raise ValueError(f"expected key/value line: {text}")
    key, value = text.split(":", 1)
    return key.strip().strip('"').strip("'"), value.strip()


def _looks_like_key_value(text: str) -> bool:
    return bool(re.match(r"^[A-Za-z0-9_.-]+\s*:", text))


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if text == "":
        return ""
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    lower = text.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("null", "none"):
        return None
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in _split_inline_list(inner)]
    try:
        if "." not in text:
            return int(text)
        return float(text)
    except ValueError:
        return text


def _split_inline_list(text: str) -> Iterable[str]:
    parts: List[str] = []
    buf: List[str] = []
    in_single = False
    in_double = False
    for char in text:
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        if char == "," and not in_single and not in_double:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(char)
    parts.append("".join(buf))
    return parts
