"""Keyword extraction and dictionary matching for probe observations."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import logging

import yaml  # type: ignore

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9._-]{1,63}")
logger = logging.getLogger(__name__)


@dataclass
class KeywordRule:
    id: str
    priority: int
    any_contains: list[str]
    any_regex: list[re.Pattern]
    infer: dict[str, str]
    confidence_delta: int
    notes: str

    def infer_summary(self) -> str:
        """Readable summary for evidence/UI."""
        parts: list[str] = []
        vendor = self.infer.get("vendor")
        product = self.infer.get("product")
        os_name = self.infer.get("os")
        category = self.infer.get("category")
        if vendor:
            parts.append(vendor)
        if product:
            parts.append(product)
        if os_name:
            parts.append(os_name)
        if category:
            parts.append(f"[{category}]")
        return " ".join(parts).strip()


class KeywordDictionary:
    """Versioned keyword dictionary loader."""

    def __init__(self, path: Path):
        self.path = path
        self.meta: dict[str, Any] = {}
        self.rules: list[KeywordRule] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.meta = {"mode": "missing"}
            self.rules = []
            logger.warning("Keyword dictionary missing at %s; running without rules", self.path)
            return
        try:
            content = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
            if not isinstance(content, dict):
                raise ValueError("keyword_dictionary root must be a mapping")
            self.meta = {
                "version": content.get("version"),
                "updated": content.get("updated"),
                "mode": "loaded",
            }
            rules_raw = content.get("rules") or []
            if not isinstance(rules_raw, list):
                raise ValueError("rules must be a list of mappings")
            parsed_rules: list[KeywordRule] = []
            for raw in rules_raw:
                try:
                    rid = str(raw["id"])
                    priority = int(raw.get("priority", 0))
                    match_block = raw.get("match") or {}
                    if not isinstance(match_block, dict):
                        raise ValueError("match must be a mapping")
                    any_contains_raw = match_block.get("any_contains", []) or []
                    any_contains = [str(x).lower() for x in any_contains_raw]
                    any_regex_raw = match_block.get("any_regex", []) or []
                    if not any_contains and not any_regex_raw:
                        raise ValueError("rule requires any_contains or any_regex")
                    any_regex = []
                    for r in any_regex_raw:
                        any_regex.append(re.compile(str(r), re.IGNORECASE))
                    infer_raw = raw.get("infer", {}) or {}
                    if not isinstance(infer_raw, dict):
                        infer_raw = {}
                    infer = {
                        k: str(v)
                        for k, v in infer_raw.items()
                        if k in {"vendor", "product", "category", "os"} and v is not None
                    }
                    confidence_delta = int(raw.get("confidence_delta", 0))
                    notes = str(raw.get("notes", "")).strip()
                    parsed_rules.append(
                        KeywordRule(
                            id=rid,
                            priority=priority,
                            any_contains=any_contains,
                            any_regex=any_regex,
                            infer={
                                k: v
                                for k, v in infer.items()
                            },
                            confidence_delta=confidence_delta,
                            notes=notes,
                        )
                    )
                except Exception as exc:
                    logger.debug("Skipping keyword rule due to parse error: %s", exc)
                    continue
            # Sort by priority desc, then id for determinism
            self.rules = sorted(parsed_rules, key=lambda r: (-r.priority, r.id))
            self.meta["rules_loaded"] = len(self.rules)
        except Exception as exc:
            self.meta = {"mode": "invalid", "error": str(exc)}
            self.rules = []
            logger.error(
                "Keyword dictionary invalid at %s; running without rules: %s",
                self.path,
                exc,
            )

    def match(self, keywords: list[str], key_fields: dict[str, Any]) -> list[dict[str, Any]]:
        """Return keyword_hits with deduped rules."""
        if not self.rules:
            return []
        hits: list[dict[str, Any]] = []
        seen_rules: set[str] = set()
        keyword_set = {kw.lower() for kw in keywords}

        # Prepare searchable text from key_fields (flattened strings)
        field_strings: list[str] = []

        def _walk(value: Any):
            if isinstance(value, str):
                field_strings.append(value.lower())
            elif isinstance(value, dict):
                for v in value.values():
                    _walk(v)
            elif isinstance(value, (list, tuple, set)):
                for v in value:
                    _walk(v)

        _walk(key_fields)

        for rule in self.rules:
            if rule.id in seen_rules:
                continue
            matched_token = None

            # any_contains over keywords and field strings
            for token in keyword_set:
                if any(term in token for term in rule.any_contains):
                    matched_token = token
                    break
            if not matched_token:
                for text in field_strings:
                    if any(term in text for term in rule.any_contains):
                        matched_token = text
                        break

            # regex fallback
            if not matched_token:
                for text in list(keyword_set) + field_strings:
                    for pattern in rule.any_regex:
                        if pattern.search(text):
                            matched_token = text
                            break
                    if matched_token:
                        break

            if matched_token:
                seen_rules.add(rule.id)
                hits.append(
                    {
                        "rule_id": rule.id,
                        "matched_token": matched_token[:128],
                        "confidence_delta": rule.confidence_delta,
                        "infer": rule.infer,
                        "infer_summary": rule.infer_summary(),
                        "priority": rule.priority,
                        "notes": rule.notes,
                    }
                )
        return hits


class KeywordExtractor:
    """Extracts normalized keywords and applies dictionary rules."""

    def __init__(self, dictionary_path: Path | None = None):
        base_path = dictionary_path or Path(__file__).parent.parent / "data" / "keyword_dictionary.yaml"
        self.dictionary = KeywordDictionary(base_path)

    def extract(self, key_fields: dict[str, Any]) -> list[str]:
        tokens: set[str] = set()

        def _add_token(token: str):
            cleaned = token.strip().lower()
            if not cleaned:
                return
            for match in _WORD_RE.finditer(cleaned):
                tokens.add(match.group(0))

        def _walk(value: Any):
            if isinstance(value, str):
                _add_token(value)
            elif isinstance(value, dict):
                for v in value.values():
                    _walk(v)
            elif isinstance(value, (list, tuple, set)):
                for v in value:
                    _walk(v)
            else:
                try:
                    as_str = json.dumps(value, ensure_ascii=False)
                    _add_token(as_str)
                except Exception:
                    pass

        _walk(key_fields)
        return sorted(tokens)

    def match_rules(self, keywords: list[str], key_fields: dict[str, Any]) -> list[dict[str, Any]]:
        return self.dictionary.match(keywords, key_fields)


def apply_confidence_delta(base_confidence: int, hits: list[dict[str, Any]]) -> tuple[int, int]:
    """Apply priority-ordered confidence deltas and clamp to [0, 100].

    Returns (new_confidence, total_delta).
    """
    if not hits:
        return base_confidence, 0
    total_delta = 0
    for hit in sorted(hits, key=lambda h: (-int(h.get("priority", 0)), h.get("rule_id", ""))):
        try:
            total_delta += int(hit.get("confidence_delta", 0))
        except Exception:
            continue
    new_conf = max(0, min(100, base_confidence + total_delta))
    return new_conf, total_delta
