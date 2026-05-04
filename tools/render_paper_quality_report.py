#!/usr/bin/env python3
"""Render PAPER_QUALITY_REPORT.json into a human-readable Markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


RUBRIC_LABELS = {
    "originality": "Originality",
    "importance": "Importance of research question",
    "claims_supported": "Claims well supported",
    "experiment_soundness": "Soundness of experiments",
    "writing_clarity": "Clarity of writing",
    "community_value": "Value to research community",
    "prior_work_context": "Contextualized relative to prior work",
}


def _text(value: Any, default: str = "not available") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip() or default
    return str(value)


def _score(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected top-level JSON object in {path}")
    return data


def _paper_title(data: dict[str, Any]) -> str:
    paper = data.get("paper")
    if isinstance(paper, dict):
        return _text(paper.get("title"))
    return "not available"


def _rubric_rows(data: dict[str, Any]) -> list[str]:
    rubric = data.get("rubric_scores")
    if not isinstance(rubric, dict):
        rubric = {}

    rows = []
    for key, label in RUBRIC_LABELS.items():
        item = rubric.get(key)
        if not isinstance(item, dict):
            item = {}
        rows.append(
            "| {label} | {score} | {confidence} | {fix} |".format(
                label=label,
                score=_score(item.get("score")),
                confidence=_text(item.get("confidence")),
                fix=_text(item.get("minimum_fix")),
            )
        )
    return rows


def _blocking_issues(data: dict[str, Any]) -> list[str]:
    issues = data.get("blocking_issues")
    if not isinstance(issues, list) or not issues:
        return ["- None reported."]

    rendered = []
    for issue in issues:
        if not isinstance(issue, dict):
            rendered.append(f"- {_text(issue)}")
            continue
        severity = _text(issue.get("severity"), "unknown")
        dimension = _text(issue.get("dimension"), "unknown")
        text = _text(issue.get("issue"))
        fix = _text(issue.get("minimum_fix"))
        evidence = _text(issue.get("evidence"))
        rendered.append(
            f"- **{severity}** ({dimension}): {text} Evidence: {evidence}. Minimum fix: {fix}"
        )
    return rendered


def _minimum_fixes(data: dict[str, Any]) -> list[str]:
    fixes = data.get("minimum_fixes")
    if not isinstance(fixes, list) or not fixes:
        return ["- None reported."]

    rendered = []
    for fix in fixes:
        if isinstance(fix, dict):
            priority = _text(fix.get("priority"), "-")
            dimension = _text(fix.get("dimension"), "general")
            fix_text = _text(fix.get("fix") or fix.get("minimum_fix"))
            rendered.append(f"- **P{priority}** ({dimension}): {fix_text}")
        else:
            rendered.append(f"- {_text(fix)}")
    return rendered


def _evidence_details(data: dict[str, Any]) -> list[str]:
    rubric = data.get("rubric_scores")
    if not isinstance(rubric, dict):
        return ["- No evidence details available."]

    lines: list[str] = []
    for key, label in RUBRIC_LABELS.items():
        item = rubric.get(key)
        if not isinstance(item, dict):
            continue
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            lines.append(f"- **{label}**: no evidence listed.")
            continue
        for ev in evidence:
            if isinstance(ev, dict):
                file = _text(ev.get("file"), "unknown file")
                location = _text(ev.get("location"), "unknown location")
                note = _text(ev.get("note"))
                lines.append(f"- **{label}**: `{file}` ({location}) - {note}")
            else:
                lines.append(f"- **{label}**: {_text(ev)}")
    return lines or ["- No evidence details available."]


def render_markdown(data: dict[str, Any]) -> str:
    """Return the Markdown rendering for a paper quality report."""
    lines = [
        "# Paper Quality Report",
        "",
        f"**Paper title**: {_paper_title(data)}",
        f"**Venue**: {_text(data.get('venue'))}",
        f"**Overall Score**: {_score(data.get('overall_score'))} / 10",
        f"**Verdict**: {_text(data.get('overall_verdict'))}",
        f"**Confidence**: {_text(data.get('overall_confidence'))}",
        f"**Generated time**: {_text(data.get('generated_at'))}",
        "",
        "## Summary",
        "",
        _text(data.get("summary")),
        "",
        "## Rubric Scores",
        "",
        "| Dimension | Score | Confidence | Minimum Fix |",
        "| --- | ---: | --- | --- |",
        *_rubric_rows(data),
        "",
        "## Blocking Issues",
        "",
        *_blocking_issues(data),
        "",
        "## Highest-Leverage Fixes",
        "",
        *_minimum_fixes(data),
        "",
        "## Evidence Details",
        "",
        *_evidence_details(data),
        "",
        "## Metadata",
        "",
        f"- **Schema version**: {_text(data.get('schema_version'))}",
        f"- **Rubric source**: {_text(data.get('rubric_source'))}",
        f"- **Reviewer model**: {_text(data.get('reviewer_model'))}",
        f"- **Reviewer reasoning**: {_text(data.get('reviewer_reasoning'))}",
        f"- **Trace path**: {_text(data.get('trace_path'), 'not available')}",
        "",
    ]
    return "\n".join(lines)


def render_file(input_path: Path, output_path: Path) -> None:
    data = _load_json(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(data), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="paper/PAPER_QUALITY_REPORT.json")
    parser.add_argument("--output", default="paper/PAPER_QUALITY_REPORT.md")
    args = parser.parse_args()

    render_file(Path(args.input), Path(args.output))
    print(f"Rendered {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

