const queryInput = document.getElementById("query-input");
const analyzeBtn = document.getElementById("analyze-btn");
const clearBtn = document.getElementById("clear-btn");
const copyBtn = document.getElementById("copy-btn");
const exampleSelect = document.getElementById("example-select");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");

const STAGE_LABELS = {
  lexical: "Lexical Analysis",
  syntax: "Syntax Analysis",
  ast: "AST",
  semantic: "Semantic Analysis",
  ir: "Intermediate Representation",
  optimization: "Optimization",
  execution_plan: "Execution Plan",
  execution: "Execution",
};

const PERFORMANCE_LABELS = {
  lexical_analysis_ms: "Lexical Analysis",
  syntax_analysis_ms: "Syntax Analysis",
  ast_construction_ms: "AST Construction",
  semantic_analysis_ms: "Semantic Analysis",
  ir_generation_ms: "IR Generation",
  optimization_ms: "Optimization",
  execution_ms: "Execution",
};

function setStatus(mode, label) {
  statusDot.className = `status-dot status-${mode}`;
  statusText.textContent = label;
}

function switchTab(tabName) {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `panel-${tabName}`);
  });
}

document.getElementById("tabs").addEventListener("click", (event) => {
  const btn = event.target.closest(".tab-btn");
  if (btn) switchTab(btn.dataset.tab);
});

exampleSelect.addEventListener("change", () => {
  if (exampleSelect.value) {
    queryInput.value = exampleSelect.value;
  }
});

clearBtn.addEventListener("click", () => {
  queryInput.value = "";
  queryInput.focus();
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(queryInput.value);
    const original = copyBtn.textContent;
    copyBtn.textContent = "Copied";
    setTimeout(() => (copyBtn.textContent = original), 1200);
  } catch (error) {
    console.error("Clipboard copy failed", error);
  }
});

async function loadSchema() {
  const container = document.getElementById("schema-tables");
  try {
    const response = await fetch("/api/schema");
    const schema = await response.json();
    container.innerHTML = "";
    Object.entries(schema).forEach(([table, columns]) => {
      const card = document.createElement("div");
      card.className = "schema-table-card";
      card.innerHTML = `
        <div class="schema-table-name">${table}</div>
        <div class="schema-table-columns">${columns.join("<br/>")}</div>
      `;
      container.appendChild(card);
    });
  } catch (error) {
    container.innerHTML = '<p class="empty-state">Schema unavailable.</p>';
  }
}

function clearPanels() {
  [
    "overview",
    "tokens",
    "ast",
    "semantic",
    "ir",
    "optimization",
    "plan",
    "result",
    "performance",
  ].forEach((name) => {
    const empty = document.getElementById(`${name}-empty`);
    if (empty) empty.classList.remove("hidden");
  });
  document.getElementById("overview-content").classList.add("hidden");
  document.getElementById("tokens-table-wrap").classList.add("hidden");
  document.getElementById("ast-content").classList.add("hidden");
  document.getElementById("semantic-content").classList.add("hidden");
  document.getElementById("ir-content").classList.add("hidden");
  document.getElementById("optimization-content").classList.add("hidden");
  document.getElementById("plan-content").classList.add("hidden");
  document.getElementById("result-table-wrap").classList.add("hidden");
  document.getElementById("result-no-rows").classList.add("hidden");
  document.getElementById("performance-content").classList.add("hidden");
}

function renderOverview(data) {
  document.getElementById("overview-empty").classList.add("hidden");
  const content = document.getElementById("overview-content");
  content.classList.remove("hidden");

  const badge = document.getElementById("overview-status-badge");
  badge.textContent = data.valid ? "VALID" : "INVALID";
  badge.className = `badge ${data.valid ? "badge-valid" : "badge-invalid"}`;

  const rows = document.getElementById("pipeline-stage-rows");
  rows.innerHTML = "";
  Object.entries(data.stages).forEach(([stage, status]) => {
    const row = document.createElement("tr");
    const symbol = status === "passed" ? "✓" : status === "failed" ? "✗" : "–";
    row.innerHTML = `<td>${STAGE_LABELS[stage] || stage}</td><td class="stage-${status}">${symbol}</td>`;
    rows.appendChild(row);
  });

  const errorBox = document.getElementById("overview-error");
  if (data.error) {
    errorBox.classList.remove("hidden");
    errorBox.innerHTML = `<span class="error-type">${data.error.type}</span>${data.error.message}`;
  } else {
    errorBox.classList.add("hidden");
  }
}

function renderTokens(tokens, data) {
  const wrap = document.getElementById("tokens-table-wrap");
  if (!tokens) {
    showSkipped("tokens", data, "Token stream");
    return;
  }
  document.getElementById("tokens-empty").classList.add("hidden");
  wrap.classList.remove("hidden");
  const rows = document.getElementById("tokens-rows");
  rows.innerHTML = "";
  tokens.forEach((token) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${escapeHtml(token.lexeme)}</td><td>${token.type}</td><td>${token.line}</td><td>${token.column}</td>`;
    rows.appendChild(row);
  });
}

function renderAst(data) {
  document.getElementById("ast-empty").classList.add("hidden");
  const content = document.getElementById("ast-content");
  content.classList.remove("hidden");

  const statusBox = document.getElementById("ast-syntax-status");
  if (data.syntax && data.syntax.status === "valid") {
    statusBox.className = "status-line ok";
    statusBox.textContent = data.syntax.message;
  } else {
    statusBox.className = "status-line";
    statusBox.textContent = data.error ? data.error.message : "Syntax could not be validated.";
  }

  const treeBox = document.getElementById("ast-tree");
  treeBox.textContent = data.ast ? data.ast.text : "AST was not constructed because syntax analysis failed.";
}

function renderSemantic(data) {
  if (!data.semantic) {
    showSkipped("semantic", data, "Semantic analysis");
    return;
  }
  document.getElementById("semantic-empty").classList.add("hidden");
  const content = document.getElementById("semantic-content");
  content.classList.remove("hidden");

  if (data.error && data.error.stage === "semantic") {
    const tableBox = document.getElementById("semantic-table-check");
    tableBox.innerHTML = `<div class="error-box"><span class="error-type">SEMANTIC ERROR</span>${escapeHtml(data.error.message)}</div>`;
    document.getElementById("semantic-select-checks").innerHTML = "";
    document.getElementById("semantic-where-checks").innerHTML = "";
    return;
  }

  const tableBox = document.getElementById("semantic-table-check");
  const selectBox = document.getElementById("semantic-select-checks");
  const whereBox = document.getElementById("semantic-where-checks");
  tableBox.innerHTML = "";
  selectBox.innerHTML = "";
  whereBox.innerHTML = "";

  const buckets = { from: tableBox, select: selectBox, where: whereBox };
  data.semantic.checks.forEach((check) => {
    const row = document.createElement("div");
    row.className = "check-row";
    row.innerHTML = `<span>${escapeHtml(check.name)}</span><span class="check-status">VALID</span>`;
    buckets[check.clause].appendChild(row);
  });

  if (!whereBox.children.length) {
    whereBox.innerHTML = '<p class="empty-state">No WHERE clause in this query.</p>';
  }
}

function skippedMessage(data, stageLabel) {
  if (!data.error) return `${stageLabel} was not produced.`;
  return `${stageLabel} was not produced because the ${data.error.stage} stage failed.`;
}

function showSkipped(name, data, stageLabel) {
  const empty = document.getElementById(`${name}-empty`);
  empty.textContent = skippedMessage(data, stageLabel);
  empty.classList.remove("hidden");
}

function renderIr(data) {
  const box = document.getElementById("ir-content");
  if (!data.ir) {
    showSkipped("ir", data, "Intermediate representation");
    return;
  }
  document.getElementById("ir-empty").classList.add("hidden");
  box.classList.remove("hidden");
  box.textContent = data.ir.text;
}

function renderOptimization(data) {
  const container = document.getElementById("optimization-content");
  if (!data.optimization) {
    showSkipped("optimization", data, "Optimizer output");
    return;
  }
  document.getElementById("optimization-empty").classList.add("hidden");
  container.classList.remove("hidden");
  container.innerHTML = "";
  data.optimization.rules.forEach((rule) => {
    const card = document.createElement("div");
    card.className = "rule-card";
    const statusClass = rule.applied ? "applied" : "not-applied";
    card.innerHTML = `
      <div class="rule-header">
        <span class="rule-name">${escapeHtml(rule.rule)}</span>
        <span class="rule-status ${statusClass}">${rule.status}</span>
      </div>
      <div class="rule-reason">${escapeHtml(rule.reason)}</div>
      <div class="rule-diff">
        <div class="rule-diff-block">
          <h4>Before</h4>
          <pre class="code-block">${escapeHtml(rule.before)}</pre>
        </div>
        <div class="rule-diff-block">
          <h4>After</h4>
          <pre class="code-block">${escapeHtml(rule.after)}</pre>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderExecutionPlan(data) {
  const content = document.getElementById("plan-content");
  if (!data.execution_plan) {
    showSkipped("plan", data, "Execution plan");
    return;
  }
  document.getElementById("plan-empty").classList.add("hidden");
  content.classList.remove("hidden");
  document.getElementById("plan-text").textContent = data.execution_plan.text;
  document.getElementById("plan-flow").textContent = `Flow: ${data.execution_plan.flow}`;
}

function renderResult(data) {
  const wrap = document.getElementById("result-table-wrap");
  const noRows = document.getElementById("result-no-rows");

  if (!data.result) {
    const message = data.error
      ? `Query was not executed. ${data.error.type}: ${data.error.message}`
      : "Query was not executed.";
    const empty = document.getElementById("result-empty");
    empty.textContent = message;
    empty.classList.remove("hidden");
    return;
  }
  document.getElementById("result-empty").classList.add("hidden");

  if (data.result.row_count === 0) {
    noRows.classList.remove("hidden");
    return;
  }

  wrap.classList.remove("hidden");
  const head = document.getElementById("result-head");
  head.innerHTML = data.result.columns.map((col) => `<th>${escapeHtml(col)}</th>`).join("");

  const rows = document.getElementById("result-rows");
  rows.innerHTML = "";
  data.result.rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = row.map((value) => `<td>${escapeHtml(String(value))}</td>`).join("");
    rows.appendChild(tr);
  });
}

function renderPerformance(data) {
  document.getElementById("performance-empty").classList.add("hidden");
  const content = document.getElementById("performance-content");
  content.classList.remove("hidden");
  document.getElementById("performance-note").textContent = data.performance.note;

  const rows = document.getElementById("performance-rows");
  rows.innerHTML = "";
  Object.entries(data.performance.timings_ms).forEach(([key, value]) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${PERFORMANCE_LABELS[key] || key}</td><td>${value.toFixed(3)}</td>`;
    rows.appendChild(row);
  });

  document.getElementById("performance-total").textContent =
    `Total Analysis Time: ${data.performance.total_ms.toFixed(3)} ms`;
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}

async function analyzeQuery() {
  const query = queryInput.value.trim();
  if (!query) {
    queryInput.focus();
    return;
  }

  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "Analyzing…";
  setStatus("loading", "Analyzing");
  clearPanels();

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await response.json();

    renderOverview(data);
    renderTokens(data.tokens, data);
    renderAst(data);
    renderSemantic(data);
    renderIr(data);
    renderOptimization(data);
    renderExecutionPlan(data);
    renderResult(data);
    renderPerformance(data);

    setStatus(data.valid ? "valid" : "invalid", data.valid ? "Valid" : "Invalid");
    if (!data.valid) switchTab("overview");
  } catch (error) {
    setStatus("invalid", "Request failed");
    console.error(error);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analyze Query";
  }
}

analyzeBtn.addEventListener("click", analyzeQuery);

queryInput.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    analyzeQuery();
  }
});

loadSchema();
