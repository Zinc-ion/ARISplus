from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "render_dashboard.py"
ASSET_DIR = REPO_ROOT / "dashboard"
MOCK_DASHBOARD = REPO_ROOT / "tests" / "fixtures" / "mock_dashboard_data.json"
TMP_ROOT = REPO_ROOT / ".tmp_test_outputs" / "dashboard"


def load_module():
    spec = importlib.util.spec_from_file_location("render_dashboard", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_static_dashboard_assets_exist() -> None:
    assert (ASSET_DIR / "index.html").exists()
    assert (ASSET_DIR / "app.js").exists()
    assert (ASSET_DIR / "style.css").exists()


def test_render_dashboard_embeds_data_without_backend() -> None:
    module = load_module()
    data = json.loads(MOCK_DASHBOARD.read_text(encoding="utf-8"))
    html = module.render_html(data, ASSET_DIR)

    assert "ARIS Coursework Demo" in html
    assert "dashboard-data" in html
    assert "Workflow Status" in html
    assert "Paper Quality" in html
    assert "Submission Readiness" in html
    assert "Blocking Items" in html
    assert "Recommended Actions" in html
    assert "Artifacts" in html
    assert "Experiments" in html
    assert "fetch(" not in html
    assert "Static dashboard data" in html
    assert "paper_quality" in html
    assert "rubric_scores" in html
    assert "blocking_items" in html
    assert "recommended_actions" in html
    assert "Submission Readiness" in html
    assert "Artifact Graph" in html
    assert "Readiness report flags one claim-support issue." in html
    assert "The paper is close to submission" in html
    assert "Resolve one ambiguous claim before submission." in html
    assert "Add one ablation for the state-center component." in html
    assert ".aris/state.json" in html
    assert ".aris/artifact_graph.json" in html


def test_mock_dashboard_data_covers_member5_display_contract() -> None:
    data = json.loads(MOCK_DASHBOARD.read_text(encoding="utf-8"))

    assert set(data["project"]) >= {"name", "summary"}

    phases = data["workflow"]["phases"]
    assert len(phases) >= 4
    for phase in phases:
        assert set(phase) >= {"name", "label", "status", "summary"}

    quality = data["paper_quality"]
    assert set(quality) >= {
        "overall_score",
        "overall_verdict",
        "overall_confidence",
        "rubric_scores",
    }
    assert set(quality["rubric_scores"]) == {
        "originality",
        "importance",
        "claims_supported",
        "experiment_soundness",
        "writing_clarity",
        "community_value",
        "prior_work_context",
    }

    submission = data["submission"]
    assert set(submission) >= {
        "status",
        "summary",
        "audits",
        "blocking_items",
        "recommended_actions",
    }

    artifacts = data["artifacts"]
    assert len(artifacts) >= 4
    for artifact in artifacts:
        assert "path" in artifact or "file" in artifact
        assert {"stage", "type", "label"} & set(artifact)

    assert set(data["experiments"]["counts"]) == {
        "queued",
        "running",
        "completed",
        "failed",
        "unknown",
    }


def test_render_dashboard_file() -> None:
    module = load_module()
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)
    output = TMP_ROOT / "dashboard" / "index.html"
    module.render_file(MOCK_DASHBOARD, output, ASSET_DIR)

    html = output.read_text(encoding="utf-8")
    assert "ARIS Coursework Demo" in html
    assert "app.js" not in html
    assert "style.css" not in html
    shutil.rmtree(TMP_ROOT)


def test_render_dashboard_tolerates_missing_sections() -> None:
    module = load_module()
    html = module.render_html({}, ASSET_DIR)

    assert "ARIS Research Dashboard" in html
    assert "dashboard-data" in html
    assert "Workflow Status" in html
    assert "unknown" in html
    assert "not available" in html
    assert "No workflow state available." in html
    assert "No audit summary available." in html
    assert "No artifacts listed." in html
    assert "fetch(" not in html


def test_render_dashboard_escapes_html_contexts() -> None:
    module = load_module()
    data = {
        "project": {
            "name": "Unsafe <Dashboard>",
            "summary": "Contains </script> marker"
        }
    }
    html = module.render_html(data, ASSET_DIR)

    assert "<title>Unsafe &lt;Dashboard&gt;</title>" in html
    assert "<h1 id=\"project-title\">Unsafe &lt;Dashboard&gt;</h1>" in html
    assert "Contains <\\/script> marker" in html
