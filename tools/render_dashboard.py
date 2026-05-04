#!/usr/bin/env python3
"""Render a static ARIS coursework dashboard from dashboard_data JSON."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSET_DIR = REPO_ROOT / "dashboard"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected top-level JSON object in {path}")
    return data


def _read_asset(asset_dir: Path, name: str) -> str:
    path = asset_dir / name
    if not path.exists():
        raise FileNotFoundError(f"Dashboard asset not found: {path}")
    return path.read_text(encoding="utf-8")


def _project_title(data: dict[str, Any]) -> str:
    project = data.get("project")
    if isinstance(project, dict):
        name = project.get("name")
        if name is not None and str(name).strip():
            return str(name).strip()
    return "ARIS Research Dashboard"


def _script_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")


def render_html(data: dict[str, Any], asset_dir: Path = DEFAULT_ASSET_DIR) -> str:
    app_js = _read_asset(asset_dir, "app.js")
    style_css = _read_asset(asset_dir, "style.css")
    data_json = _script_json(data)
    title = _project_title(data)
    title_html = html.escape(title, quote=True)

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{title_html}</title>
  <style>
{style_css}
  </style>
</head>
<body>
  <main class=\"shell\">
    <section class=\"hero\">
      <p class=\"eyebrow\">ARIS Research Workflow</p>
      <h1 id=\"project-title\">{title_html}</h1>
      <p id=\"project-summary\" class=\"summary\">Loading dashboard data...</p>
    </section>

    <section class=\"grid\">
      <article class=\"card wide\">
        <h2>Workflow Status</h2>
        <div id=\"workflow-list\" class=\"timeline\"></div>
      </article>

      <article class=\"card score-card\">
        <h2>Paper Quality</h2>
        <div id=\"quality-score\" class=\"score\">unknown</div>
        <p id=\"quality-verdict\" class=\"muted\">not available</p>
      </article>

      <article class=\"card\">
        <h2>Rubric Scores</h2>
        <div id=\"rubric-grid\" class=\"rubric-grid\"></div>
      </article>

      <article class=\"card\">
        <h2>Submission Readiness</h2>
        <p id=\"submission-status\" class=\"status-pill\">unknown</p>
        <h3>Audits</h3>
        <div id=\"audit-list\" class=\"list\"></div>
        <h3>Blocking Items</h3>
        <div id=\"blocking-list\" class=\"list compact\"></div>
        <h3>Recommended Actions</h3>
        <div id=\"action-list\" class=\"list compact\"></div>
      </article>

      <article class=\"card\">
        <h2>Artifacts</h2>
        <div id=\"artifact-list\" class=\"list\"></div>
      </article>

      <article class=\"card\">
        <h2>Experiments</h2>
        <div id=\"experiment-summary\" class=\"metric-row\"></div>
      </article>
    </section>
  </main>

  <script id=\"dashboard-data\" type=\"application/json\">
{data_json}
  </script>
  <script>
{app_js}
  </script>
</body>
</html>
"""


def render_file(input_path: Path, output_path: Path, asset_dir: Path = DEFAULT_ASSET_DIR) -> None:
    data = _load_json(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html(data, asset_dir), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=".aris/dashboard_data.json")
    parser.add_argument("--output", default="dashboard/index.html")
    parser.add_argument("--asset-dir", default=str(DEFAULT_ASSET_DIR))
    args = parser.parse_args()

    render_file(Path(args.input), Path(args.output), Path(args.asset_dir))
    print(f"Rendered {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

