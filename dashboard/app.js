(function () {
  const RUBRIC_LABELS = {
    originality: "Originality",
    importance: "Importance",
    claims_supported: "Claims Supported",
    experiment_soundness: "Experiment Soundness",
    writing_clarity: "Writing Clarity",
    community_value: "Community Value",
    prior_work_context: "Prior Work Context"
  };

  function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function text(value, fallback) {
    if (value === undefined || value === null) return fallback || "not available";
    if (Array.isArray(value) && value.length === 0) return fallback || "not available";
    if (typeof value === "string" && value.trim() === "") return fallback || "not available";
    return String(value);
  }

  function score(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "unknown";
    return Number.isInteger(number) ? String(number) : number.toFixed(1);
  }

  function statusClass(value) {
    return text(value, "unknown").toLowerCase().replace(/[^a-z0-9_-]+/g, "-");
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function clear(element) {
    if (element) element.textContent = "";
  }

  function node(tag, className, content) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content !== undefined) element.textContent = content;
    return element;
  }

  function appendMessage(target, message) {
    if (!target) return;
    const item = node("p", "muted", message);
    target.appendChild(item);
  }

  function appendListRow(target, left, right) {
    if (!target) return;
    const row = node("div", "list-row");
    row.appendChild(node("span", "", left));
    row.appendChild(node("strong", "", right));
    target.appendChild(row);
  }

  function listFrom(value) {
    return Array.isArray(value) ? value : [];
  }

  function loadData() {
    const script = byId("dashboard-data");
    if (!script) return {};
    try {
      const parsed = JSON.parse(script.textContent || "{}");
      if (isRecord(parsed)) return parsed;
      return { project: { name: "Dashboard data error", summary: "Top-level dashboard data must be an object." } };
    } catch (error) {
      return { project: { name: "Dashboard data error", summary: "Could not parse embedded dashboard JSON." } };
    }
  }

  function renderWorkflow(data) {
    const target = byId("workflow-list");
    if (!target) return;
    clear(target);

    const workflow = isRecord(data.workflow) ? data.workflow : {};
    const phases = listFrom(workflow.phases);
    if (!phases.length) {
      appendMessage(target, "No workflow state available.");
      return;
    }

    phases.forEach((phaseValue) => {
      const phase = isRecord(phaseValue) ? phaseValue : {};
      const status = text(phase.status, "unknown");
      const row = node("div", `phase ${statusClass(status)}`);
      row.appendChild(node("span", "dot"));

      const body = node("div");
      body.appendChild(node("strong", "", text(phase.label || phase.name, "unknown")));
      body.appendChild(node("p", "", text(phase.summary, "not available")));
      row.appendChild(body);
      row.appendChild(node("span", "tag", status));
      target.appendChild(row);
    });
  }

  function renderQuality(data) {
    const quality = isRecord(data.paper_quality) ? data.paper_quality : {};
    const scoreTarget = byId("quality-score");
    if (scoreTarget) scoreTarget.textContent = score(quality.overall_score);

    const verdictTarget = byId("quality-verdict");
    if (verdictTarget) {
      verdictTarget.textContent =
        `${text(quality.overall_verdict, "unknown")} | confidence: ${text(quality.overall_confidence, "unknown")}`;
    }

    const rubricTarget = byId("rubric-grid");
    if (!rubricTarget) return;
    clear(rubricTarget);
    const rubric = isRecord(quality.rubric_scores) ? quality.rubric_scores : {};

    Object.keys(RUBRIC_LABELS).forEach((key) => {
      const item = isRecord(rubric[key]) ? rubric[key] : {};
      const row = node("div", "rubric-item");
      row.appendChild(node("span", "", RUBRIC_LABELS[key]));
      row.appendChild(node("strong", "", score(item.score)));
      row.appendChild(node("small", "", text(item.minimum_fix, "not available")));
      rubricTarget.appendChild(row);
    });
  }

  function itemText(item, fields) {
    if (!isRecord(item)) return text(item, "not available");
    for (const field of fields) {
      if (item[field] !== undefined && item[field] !== null && item[field] !== "") {
        return text(item[field], "not available");
      }
    }
    return "not available";
  }

  function renderSimpleList(targetId, items, fields, emptyMessage) {
    const target = byId(targetId);
    if (!target) return;
    clear(target);
    if (!items.length) {
      appendMessage(target, emptyMessage);
      return;
    }
    items.forEach((item) => {
      const row = node("div", "list-row single");
      row.appendChild(node("span", "", itemText(item, fields)));
      target.appendChild(row);
    });
  }

  function renderSubmission(data) {
    const submission = isRecord(data.submission) ? data.submission : {};
    const status = text(submission.status || submission.overall_status, "unknown");
    const statusEl = byId("submission-status");
    if (statusEl) {
      statusEl.textContent = status;
      statusEl.className = `status-pill ${statusClass(status)}`;
    }

    const auditTarget = byId("audit-list");
    if (auditTarget) {
      clear(auditTarget);
      const audits = listFrom(submission.audits);
      if (!audits.length) {
        appendMessage(auditTarget, "No audit summary available.");
      } else {
        audits.forEach((auditValue) => {
          const audit = isRecord(auditValue) ? auditValue : {};
          appendListRow(
            auditTarget,
            text(audit.name || audit.audit, "unknown"),
            text(audit.verdict || audit.status, "unknown")
          );
        });
      }
    }

    const blockingItems = listFrom(submission.blocking_items);
    const recommendedActions = listFrom(submission.recommended_actions);
    renderSimpleList(
      "blocking-list",
      blockingItems,
      ["item", "issue", "summary", "description", "fix"],
      "None reported."
    );
    renderSimpleList(
      "action-list",
      recommendedActions,
      ["action", "fix", "summary", "description", "item"],
      "None reported."
    );
  }

  function renderArtifacts(data) {
    const target = byId("artifact-list");
    if (!target) return;
    clear(target);
    const artifacts = listFrom(data.artifacts).slice(0, 8);
    if (!artifacts.length) {
      appendMessage(target, "No artifacts listed.");
      return;
    }
    artifacts.forEach((artifactValue) => {
      const artifact = isRecord(artifactValue) ? artifactValue : {};
      appendListRow(
        target,
        text(artifact.path || artifact.file || artifact.label, "unknown"),
        text(artifact.stage || artifact.type, "artifact")
      );
    });
  }

  function renderExperiments(data) {
    const target = byId("experiment-summary");
    if (!target) return;
    clear(target);
    const experiments = isRecord(data.experiments) ? data.experiments : {};
    const counts = isRecord(experiments.counts) ? experiments.counts : experiments;
    const keys = ["queued", "running", "completed", "failed", "unknown"];

    keys.forEach((key) => {
      const metric = node("div", "metric");
      metric.appendChild(node("strong", "", text(counts[key], "0")));
      metric.appendChild(node("span", "", key));
      target.appendChild(metric);
    });
  }

  function render() {
    const data = loadData();
    const project = isRecord(data.project) ? data.project : {};
    const titleTarget = byId("project-title");
    const summaryTarget = byId("project-summary");
    if (titleTarget) titleTarget.textContent = text(project.name, "unknown");
    if (summaryTarget) summaryTarget.textContent = text(project.summary, "not available");
    renderWorkflow(data);
    renderQuality(data);
    renderSubmission(data);
    renderArtifacts(data);
    renderExperiments(data);
  }

  render();
})();
