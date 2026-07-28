const state = {
  projects: [],
  selectedId: null,
};

const projectList = document.querySelector("#project-list");
const projectCount = document.querySelector("#project-count");
const detailPanel = document.querySelector("#detail-panel");
const scanForm = document.querySelector("#scan-form");
const scanSubmit = document.querySelector("#scan-submit");
const formStatus = document.querySelector("#form-status");

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || `请求失败：${response.status}`);
  }
  return payload;
}

async function loadProjects(selectFirst = false) {
  const payload = await request("/api/projects");
  state.projects = payload.projects;
  projectCount.textContent = state.projects.length;
  renderProjects();
  if (selectFirst && !state.selectedId && state.projects.length) {
    await selectProject(state.projects[0].id);
  }
}

function renderProjects() {
  if (!state.projects.length) {
    projectList.innerHTML = '<p class="empty-note">还没有项目。</p>';
    return;
  }
  projectList.innerHTML = state.projects
    .map((project) => `
      <button
        class="project-item ${project.id === state.selectedId ? "active" : ""}"
        data-project-id="${project.id}"
        type="button"
      >
        <strong>${escapeHtml(project.name)}</strong>
        <span>${project.open_finding_count}</span>
        <small>${escapeHtml(project.scope_host)}</small>
        <small>${project.asset_count} 资产</small>
      </button>
    `)
    .join("");
}

async function selectProject(projectId) {
  state.selectedId = Number(projectId);
  renderProjects();
  detailPanel.innerHTML = `
    <div class="empty-state">
      <span class="empty-index">···</span>
      <h2>读取资产账本</h2>
    </div>
  `;
  const [detail, knowledge] = await Promise.all([
    request(`/api/projects/${state.selectedId}`),
    request("/api/knowledge"),
  ]);
  renderDetail(detail, knowledge.items);
}

function renderDetail(detail, knowledge) {
  const { project, stats, assets, findings, runs, jobs } = detail;
  const latestRun = runs[0];
  const runSummary = latestRun?.summary_json || {};
  detailPanel.innerHTML = `
    <div class="detail-head">
      <div>
        <h2>${escapeHtml(project.name)}</h2>
        <a href="${escapeHtml(project.root_url)}" target="_blank" rel="noreferrer">
          ${escapeHtml(project.root_url)}
        </a>
      </div>
      <button class="rescan-button" type="button" data-rescan="${project.id}">
        <span>继续分析</span><span>↻</span>
      </button>
    </div>
    <div class="stats">
      ${stat(stats.assets, "全部资产")}
      ${stat(stats.javascript, "JavaScript")}
      ${stat(stats.open_findings, "开放发现")}
      ${stat(stats.runs, "扫描批次")}
    </div>
    ${latestRun ? `
      <div class="run-strip">
        最近批次 #${latestRun.id}：
        新分析 ${runSummary.analyzed_jobs || 0} 项，
        复用 ${runSummary.reused_jobs || 0} 项，
        新版本 ${runSummary.new_revisions || 0} 个。
      </div>
    ` : ""}
    <div class="section-head">
      <h3>资产账本</h3>
      <span>内容摘要用于判断是否需要重跑</span>
    </div>
    ${renderAssets(assets)}
    <div class="section-head">
      <h3>检测覆盖</h3>
      <span>最近 ${jobs.length} 条任务记录</span>
    </div>
    ${renderJobs(jobs)}
    <div class="section-head">
      <h3>安全发现</h3>
      <span>${findings.length} 个开放项</span>
    </div>
    ${renderFindings(findings)}
    <div class="section-head">
      <h3>知识审核</h3>
      <span>批准后才会写入项目 Skill</span>
    </div>
    ${renderKnowledge(knowledge)}
  `;
}

function stat(value, label) {
  return `<div class="stat"><strong>${value}</strong><span>${label}</span></div>`;
}

function renderAssets(assets) {
  if (!assets.length) {
    return '<p class="empty-note">尚未发现资产。</p>';
  }
  return `
    <table class="asset-table">
      <thead>
        <tr><th style="width: 18%">类型</th><th>URL</th><th style="width: 18%">摘要</th><th style="width: 12%">状态</th></tr>
      </thead>
      <tbody>
        ${assets.map((asset) => `
          <tr>
            <td><span class="kind-pill">${escapeHtml(asset.kind)}</span></td>
            <td><span class="asset-url" title="${escapeHtml(asset.canonical_url)}">${escapeHtml(asset.canonical_url)}</span></td>
            <td>${asset.content_sha256 ? escapeHtml(asset.content_sha256.slice(0, 10)) : "—"}</td>
            <td>${escapeHtml(asset.state)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderFindings(findings) {
  if (!findings.length) {
    return '<p class="empty-note">当前没有开放的安全发现。</p>';
  }
  return `
    <div class="findings">
      ${findings.map((finding) => `
        <article class="finding">
          <span class="severity ${escapeHtml(finding.severity)}">${escapeHtml(finding.severity)}</span>
          <div>
            <h4>${escapeHtml(finding.title)}</h4>
            <p>${escapeHtml(finding.asset_url)}</p>
            <p>${escapeHtml(finding.evidence)}</p>
          </div>
          <button class="promote-button" type="button" data-promote="${finding.id}">
            晋升知识
          </button>
        </article>
      `).join("")}
    </div>
  `;
}

function renderJobs(jobs) {
  if (!jobs.length) {
    return '<p class="empty-note">尚无检测任务。</p>';
  }
  return `
    <table class="asset-table coverage-table">
      <thead>
        <tr><th style="width: 14%">批次</th><th>资产</th><th style="width: 23%">检测器</th><th style="width: 14%">结果</th></tr>
      </thead>
      <tbody>
        ${jobs.map((job) => `
          <tr>
            <td>#${job.run_id}</td>
            <td>
              <span class="asset-url" title="${escapeHtml(job.asset_url)}">
                ${escapeHtml(job.asset_url)}
              </span>
            </td>
            <td>${escapeHtml(job.detector_key)} <small>v${escapeHtml(job.detector_version)}</small></td>
            <td><span class="job-status ${escapeHtml(job.status)}">${escapeHtml(job.status)}</span></td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderKnowledge(items) {
  if (!items.length) {
    return '<p class="empty-note">还没有待审核或已批准的通用模式。</p>';
  }
  return `
    <div class="knowledge-list">
      ${items.map((item) => `
        <div class="knowledge-item">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <span>${escapeHtml(item.detector_key)} · ${escapeHtml(item.category)}</span>
          </div>
          ${item.status === "draft"
            ? `<button type="button" data-approve="${item.id}">审核并写入 Skill</button>`
            : '<span class="approved-label">已批准</span>'}
        </div>
      `).join("")}
    </div>
  `;
}

async function runExistingProject(projectId, button) {
  button.disabled = true;
  button.querySelector("span").textContent = "分析中";
  try {
    await request(`/api/projects/${projectId}/scans`, { method: "POST" });
    await loadProjects();
    await selectProject(projectId);
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
  }
}

scanForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  scanSubmit.disabled = true;
  formStatus.classList.remove("error");
  formStatus.textContent = "正在抓取页面并计算资产版本…";
  const form = new FormData(scanForm);
  try {
    const result = await request("/api/scans", {
      method: "POST",
      body: JSON.stringify({
        url: form.get("url"),
        name: form.get("name"),
      }),
    });
    const projectId = result.project.project.id;
    formStatus.textContent = `批次 #${result.run.id} 已完成。`;
    await loadProjects();
    await selectProject(projectId);
  } catch (error) {
    formStatus.classList.add("error");
    formStatus.textContent = error.message;
  } finally {
    scanSubmit.disabled = false;
  }
});

projectList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-project-id]");
  if (button) {
    selectProject(button.dataset.projectId).catch((error) => alert(error.message));
  }
});

detailPanel.addEventListener("click", async (event) => {
  const rescan = event.target.closest("[data-rescan]");
  if (rescan) {
    await runExistingProject(Number(rescan.dataset.rescan), rescan);
    return;
  }
  const promote = event.target.closest("[data-promote]");
  if (promote) {
    promote.disabled = true;
    try {
      await request(`/api/findings/${promote.dataset.promote}/promote`, {
        method: "POST",
      });
      await selectProject(state.selectedId);
    } catch (error) {
      promote.disabled = false;
      alert(error.message);
    }
    return;
  }
  const approve = event.target.closest("[data-approve]");
  if (approve) {
    approve.disabled = true;
    try {
      await request(`/api/knowledge/${approve.dataset.approve}/approve`, {
        method: "POST",
      });
      await selectProject(state.selectedId);
    } catch (error) {
      approve.disabled = false;
      alert(error.message);
    }
  }
});

loadProjects(true).catch((error) => {
  formStatus.classList.add("error");
  formStatus.textContent = error.message;
});
