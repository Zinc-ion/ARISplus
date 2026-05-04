from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "render_paper_quality_report.py"
MOCK_REPORT = REPO_ROOT / "tests" / "fixtures" / "mock_paper_quality_report.json"
TMP_ROOT = REPO_ROOT / ".tmp_test_outputs" / "paper_quality_renderer"


def load_module():
    spec = importlib.util.spec_from_file_location("render_paper_quality_report", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_markdown_contains_all_rubric_dimensions() -> None:
    module = load_module()
    data = json.loads(MOCK_REPORT.read_text(encoding="utf-8"))
    markdown = module.render_markdown(data)

    assert "# Paper Quality Report" in markdown
    assert "**Paper title**:" in markdown
    assert "Structured Research Agents" in markdown
    assert "**Venue**: ICLR" in markdown
    assert "Overall Score" in markdown
    assert "**Verdict**: almost" in markdown
    assert "**Confidence**: medium" in markdown
    assert "**Generated time**: 2026-05-04T12:00:00Z" in markdown
    assert "## Summary" in markdown
    assert "## Blocking Issues" in markdown
    assert "## Highest-Leverage Fixes" in markdown
    assert "## Evidence Details" in markdown
    assert "## Metadata" in markdown
    for label in module.RUBRIC_LABELS.values():
        assert label in markdown
    assert "medium" in markdown
    assert "Clarify which part is new" in markdown
    assert "One quality-improvement claim" in markdown
    assert "Resolve the ambiguous numeric claim" in markdown
    assert "- **Schema version**: 1" in markdown
    assert "- **Rubric source**: stanford_agentic_reviewer_style" in markdown
    assert "- **Reviewer model**: gpt-5.4" in markdown
    assert "- **Reviewer reasoning**: xhigh" in markdown
    assert "- **Trace path**: .aris/traces/paper-quality-eval/20260504_run01/" in markdown


def test_render_markdown_tolerates_missing_fields() -> None:
    module = load_module()
    markdown = module.render_markdown({})

    assert "# Paper Quality Report" in markdown
    assert "**Paper title**: not available" in markdown
    assert "**Venue**: not available" in markdown
    assert "**Overall Score**: unknown / 10" in markdown
    assert "**Verdict**: not available" in markdown
    assert "**Confidence**: not available" in markdown
    assert "**Generated time**: not available" in markdown
    assert "unknown" in markdown
    assert "not available" in markdown
    assert "- None reported." in markdown
    assert "- No evidence details available." in markdown
    for label in module.RUBRIC_LABELS.values():
        assert label in markdown


def test_render_file_writes_markdown() -> None:
    module = load_module()
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)
    output = TMP_ROOT / "nested" / "PAPER_QUALITY_REPORT.md"
    module.render_file(MOCK_REPORT, output)

    text = output.read_text(encoding="utf-8")
    assert "Paper Quality Report" in text
    assert "Rubric Scores" in text
    shutil.rmtree(TMP_ROOT)
