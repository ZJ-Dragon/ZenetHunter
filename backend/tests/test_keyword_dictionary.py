import tempfile
from pathlib import Path

from app.services.keyword_extractor import KeywordExtractor, apply_confidence_delta


def _write_dict(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "dict.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_keyword_dictionary_matches_contains_and_dedup(tmp_path: Path):
    yaml_body = """
version: "1.0.0"
updated: "test"
rules:
  - id: rule-one
    priority: 50
    match:
      any_contains: ["hyperos", "miui"]
    infer:
      vendor: "Xiaomi"
    confidence_delta: 10
    notes: "HyperOS hint"
"""
    path = _write_dict(tmp_path, yaml_body)
    extractor = KeywordExtractor(dictionary_path=path)
    keywords = ["HyperOS", "hyperos"]  # duplicate tokens
    key_fields = {"http_title": "HyperOS Phone"}

    hits = extractor.match_rules(keywords, key_fields)
    assert len(hits) == 1
    assert hits[0]["rule_id"] == "rule-one"
    assert hits[0]["confidence_delta"] == 10
    assert hits[0]["infer"]["vendor"] == "Xiaomi"
    assert hits[0]["infer_summary"] == "Xiaomi"


def test_keyword_dictionary_priority_and_regex(tmp_path: Path):
    yaml_body = """
version: "1.0.0"
updated: "test"
rules:
  - id: low
    priority: 10
    match:
      any_contains: ["mi."]
    confidence_delta: 1
    notes: "low"
  - id: high-regex
    priority: 80
    match:
      any_regex: ["mi\\\\.[a-z0-9]+\\\\.[a-z0-9]+"]
    confidence_delta: 15
    notes: "regex"
"""
    path = _write_dict(tmp_path, yaml_body)
    extractor = KeywordExtractor(dictionary_path=path)
    keywords = ["mi.device.model"]
    hits = extractor.match_rules(keywords, {"http_title": "mi.device.model"})
    assert len(hits) == 2
    hits_sorted = sorted(hits, key=lambda h: (-h.get("priority", 0), h["rule_id"]))
    assert hits_sorted[0]["rule_id"] == "high-regex"
    new_conf, delta = apply_confidence_delta(90, hits)
    assert delta == 16
    assert new_conf == 100  # clamped


def test_apply_confidence_delta_clamp_lower_and_upper():
    hits = [
        {"priority": 100, "confidence_delta": 15, "rule_id": "a"},
        {"priority": 90, "confidence_delta": -10, "rule_id": "b"},
    ]
    new_conf, delta = apply_confidence_delta(5, hits)
    assert delta == 5
    assert new_conf == 10  # 5+5 clamped above 0


def test_keyword_dictionary_invalid_file_disables_rules(tmp_path: Path):
    yaml_body = """
- not-a-dict
"""
    path = _write_dict(tmp_path, yaml_body)
    extractor = KeywordExtractor(dictionary_path=path)
    assert extractor.dictionary.meta.get("mode") == "invalid"
    hits = extractor.match_rules(["demo"], {"http_title": "demo"})
    assert hits == []
