'use strict';

// ─── State ────────────────────────────────────────────────────────────────────
const state = {
  profile:    null,   // ParsedResume from /api/upload-resume
  jobTitle:   null,   // final search title
  jobs:       [],     // list[MatchedJob] from /api/search-jobs
  panelIdx:   null,   // index into state.jobs for open panel
  tabCache:   {},     // { jobIdx: { tailor?, research?, interview? } }
};

// ─── API helpers ──────────────────────────────────────────────────────────────
async function parseResponse(res) {
  const ct = res.headers.get('content-type') ?? '';
  if (ct.includes('application/json')) {
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail ?? `Server error ${res.status}`);
    return data;
  }
  // Non-JSON body (unexpected plain-text 500, etc.)
  const text = await res.text();
  throw new Error(res.ok ? 'Unexpected non-JSON response' : `Server error ${res.status}: ${text.slice(0, 120)}`);
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  return parseResponse(res);
}

async function postForm(url, formData) {
  const res = await fetch(url, { method: 'POST', body: formData });
  return parseResponse(res);
}

async function getJSON(url) {
  const res = await fetch(url);
  return parseResponse(res);
}

// ─── UI helpers ───────────────────────────────────────────────────────────────
function show(id)  { document.getElementById(id).classList.remove('hidden'); }
function hide(id)  { document.getElementById(id).classList.add('hidden'); }
function el(id)    { return document.getElementById(id); }

function setStatus(id, msg, isError = false) {
  const el_ = el(id);
  el_.textContent = msg;
  el_.className = 'status-msg' + (isError ? ' error' : '');
  el_.classList.remove('hidden');
}

function spinner(label = 'Loading…') {
  return `<span class="spinner"></span>${label}`;
}

function scoreBadgeClass(score) {
  if (score >= 70) return 'score-high';
  if (score >= 50) return 'score-mid';
  return 'score-low';
}

// ─── Upload ───────────────────────────────────────────────────────────────────
el('upload-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = el('upload-btn');
  btn.disabled = true;
  btn.textContent = 'Analysing…';
  setStatus('upload-status', spinner('Parsing your resume with AI…'));

  try {
    const fd = new FormData(e.target);
    const result = await postForm('/api/upload-resume', fd);

    state.profile   = result.profile;
    state.jobTitle  = result.job_title ?? null;

    if (result.job_title) {
      // Title was provided → go straight to search
      setStatus('upload-status', `Resume parsed. Searching for "${result.job_title}"…`);
      await runSearch(result.job_title);
    } else {
      // Show inferred roles for user to pick
      hide('upload-status');
      renderRoles(result.inferred_roles);
      show('roles-section');
    }
  } catch (err) {
    setStatus('upload-status', `Error: ${err.message}`, true);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Analyse Resume';
  }
});

function renderRoles(roles) {
  const container = el('roles-list');
  container.innerHTML = '';
  roles.forEach(role => {
    const btn = document.createElement('button');
    btn.className = 'role-btn';
    btn.textContent = role;
    btn.addEventListener('click', async () => {
      state.jobTitle = role;
      hide('roles-section');
      await runSearch(role);
    });
    container.appendChild(btn);
  });
}

// ─── Job Search ───────────────────────────────────────────────────────────────
async function runSearch(title) {
  el('jobs-heading').textContent = `3. Matched Jobs — "${title}"`;
  el('jobs-count').textContent = '';
  el('jobs-grid').innerHTML = '';
  setStatus('jobs-status', spinner(`Searching all job boards for "${title}"…`));
  show('jobs-section');

  try {
    const result = await postJSON('/api/search-jobs', {
      job_title: title,
      location:  '',
      profile:   state.profile,
    });

    state.jobs = result.jobs;
    hide('jobs-status');
    el('jobs-count').textContent = `${result.total} jobs`;
    renderJobs(result.jobs);
  } catch (err) {
    setStatus('jobs-status', `Search failed: ${err.message}`, true);
  }
}

function renderJobs(jobs) {
  const grid = el('jobs-grid');
  grid.innerHTML = '';
  if (!jobs.length) {
    grid.innerHTML = '<p class="empty-state">No jobs found. Try a different title or location.</p>';
    return;
  }

  jobs.forEach((matched, idx) => {
    const { listing, score } = matched;
    const card = document.createElement('div');
    card.className = 'job-card';
    card.dataset.idx = idx;

    const topStrengths = (score.strengths ?? []).slice(0, 2);
    const topMissing   = (score.missing_skills ?? []).slice(0, 2);

    const tagHTML = [
      ...topStrengths.map(s => `<span class="tag">${escHtml(s)}</span>`),
      ...topMissing.map(m  => `<span class="tag missing">Missing: ${escHtml(m)}</span>`),
    ].join('');

    card.innerHTML = `
      <div class="job-card-left">
        <div class="job-card-title">${escHtml(listing.title)}</div>
        <div class="job-card-company">${escHtml(listing.company)}</div>
        <div class="job-card-meta">
          ${escHtml(listing.location || 'Location not specified')}
          &nbsp;·&nbsp; via ${escHtml(listing.source)}
          ${listing.salary_min ? ` &nbsp;·&nbsp; $${listing.salary_min.toLocaleString()}${listing.salary_max ? '–$' + listing.salary_max.toLocaleString() : '+'}` : ''}
        </div>
        <div class="job-card-tags">${tagHTML}</div>
      </div>
      <div class="job-card-right">
        <span class="score-badge ${scoreBadgeClass(score.score)}">${score.score}%</span>
      </div>`;

    card.addEventListener('click', () => openPanel(idx));
    grid.appendChild(card);
  });
}

// ─── Panel ────────────────────────────────────────────────────────────────────
function openPanel(idx) {
  state.panelIdx = idx;
  const { listing, score } = state.jobs[idx];

  el('panel-title').textContent = listing.title;
  el('panel-meta').textContent  = `${listing.company}${listing.location ? ' · ' + listing.location : ''}`;
  el('panel-score-badge').textContent  = `${score.score}%`;
  el('panel-score-badge').className    = `score-badge ${scoreBadgeClass(score.score)}`;

  const saveBtn = el('panel-save-btn');
  saveBtn.disabled = false;
  saveBtn.textContent = 'Save to Tracker';

  // Render summary tab immediately
  renderSummaryTab(score);
  switchTab('summary');
  show('panel-overlay');
  document.body.style.overflow = 'hidden';
}

function closePanel() {
  hide('panel-overlay');
  document.body.style.overflow = '';
  state.panelIdx = null;
}

el('panel-close-btn').addEventListener('click', closePanel);
el('panel-overlay').addEventListener('click', (e) => {
  if (e.target === el('panel-overlay')) closePanel();
});

// Tab switching
el('panel-tabs').addEventListener('click', async (e) => {
  const btn = e.target.closest('.tab-btn');
  if (!btn) return;
  const tab = btn.dataset.tab;
  switchTab(tab);
  await lazyLoadTab(tab);
});

function switchTab(tab) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  ['summary', 'tailor', 'research', 'interview'].forEach(t => {
    el(`tab-${t}`).classList.toggle('hidden', t !== tab);
  });
}

async function lazyLoadTab(tab) {
  const idx = state.panelIdx;
  if (idx === null) return;
  if (tab === 'summary') return;                         // already rendered
  if (state.tabCache[idx]?.[tab]) return;                // already fetched

  const pane = el(`tab-${tab}`);
  const { listing } = state.jobs[idx];

  pane.innerHTML = spinner(`Loading ${tab}…`);

  try {
    let data;
    if (tab === 'tailor') {
      data = await postJSON('/api/jobs/tailor', { job: listing, profile: state.profile });
      state.tabCache[idx] = { ...state.tabCache[idx], tailor: data };
      renderTailorTab(data, pane);
    } else if (tab === 'research') {
      data = await postJSON('/api/jobs/research', { job: listing });
      state.tabCache[idx] = { ...state.tabCache[idx], research: data };
      renderResearchTab(data, pane);
    } else if (tab === 'interview') {
      data = await postJSON('/api/jobs/interview-prep', { job: listing, profile: state.profile });
      state.tabCache[idx] = { ...state.tabCache[idx], interview: data };
      renderInterviewTab(data, pane);
    }
  } catch (err) {
    pane.innerHTML = `<p class="status-msg error">Failed to load: ${escHtml(err.message)}</p>`;
  }
}

// ── Summary tab ───────────────────────────────────────────────────────────────
function renderSummaryTab(score) {
  const pane = el('tab-summary');
  const strengths = (score.strengths ?? []).map(s => `<li>${escHtml(s)}</li>`).join('');
  const missing   = (score.missing_skills ?? []).map(m => `<li>${escHtml(m)}</li>`).join('');

  pane.innerHTML = `
    <div class="summary-score ${scoreBadgeClass(score.score)}" style="color:#fff;display:inline-block;padding:0.2rem 0.75rem;border-radius:6px;margin-bottom:0.5rem">${score.score}% match</div>
    <p class="summary-blurb">${escHtml(score.summary ?? '')}</p>
    ${strengths ? `<div class="signal-group"><h4>Strengths</h4><ul class="signal-list strengths">${strengths}</ul></div>` : ''}
    ${missing   ? `<div class="signal-group"><h4>Skill Gaps</h4><ul class="signal-list missing">${missing}</ul></div>` : ''}
    <a href="${escHtml(state.jobs[state.panelIdx].listing.url)}" target="_blank" rel="noopener noreferrer" class="load-btn" style="text-align:center;text-decoration:none;margin-top:1rem">View Job Posting ↗</a>`;
}

// ── Tailor tab ────────────────────────────────────────────────────────────────
function renderTailorTab(data, pane) {
  const rows = (data.original_bullets ?? []).map((orig, i) => `
    <tr>
      <td>${escHtml(orig)}</td>
      <td>${escHtml((data.tailored_bullets ?? [])[i] ?? '')}</td>
    </tr>`).join('');

  pane.innerHTML = `
    <h4 style="margin-bottom:0.5rem;font-size:0.85rem;font-weight:700;text-transform:uppercase;color:var(--muted)">Resume Bullets — Before &amp; After</h4>
    <table class="diff-table">
      <thead><tr><th>Original</th><th>Tailored for this role</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <h4 style="margin:1.5rem 0 0.5rem;font-size:0.85rem;font-weight:700;text-transform:uppercase;color:var(--muted)">Cover Letter</h4>
    <div class="cover-letter-box">${escHtml(data.cover_letter ?? '')}</div>`;
}

// ── Research tab ──────────────────────────────────────────────────────────────
function renderResearchTab(data, pane) {
  const greens = (data.green_flags ?? []).map(f => `<li>${escHtml(f)}</li>`).join('');
  const reds   = (data.red_flags   ?? []).map(f => `<li>${escHtml(f)}</li>`).join('');

  pane.innerHTML = `
    <div class="snapshot-box">${escHtml(data.snapshot ?? '')}</div>
    ${greens ? `<div class="signal-group"><h4>Green Flags</h4><ul class="signal-list green-flags">${greens}</ul></div>` : ''}
    ${reds   ? `<div class="signal-group"><h4>Red Flags</h4><ul class="signal-list red-flags">${reds}</ul></div>`   : ''}`;
}

// ── Interview tab ─────────────────────────────────────────────────────────────
function renderInterviewTab(data, pane) {
  const cards = (data.qa_pairs ?? []).map((qa, i) => `
    <div class="qa-card" data-qi="${i}">
      <div class="qa-question">
        <span>${escHtml(qa.question)}</span>
        <span class="qa-chevron">▼</span>
      </div>
      <div class="qa-answer hidden">${escHtml(qa.answer)}</div>
    </div>`).join('');

  pane.innerHTML = `<div class="qa-list">${cards}</div>`;

  pane.querySelectorAll('.qa-question').forEach(q => {
    q.addEventListener('click', () => {
      const card   = q.closest('.qa-card');
      const answer = card.querySelector('.qa-answer');
      const isOpen = !answer.classList.contains('hidden');
      answer.classList.toggle('hidden', isOpen);
      card.classList.toggle('open', !isOpen);
    });
  });
}

// ─── Save to Tracker ──────────────────────────────────────────────────────────
el('panel-save-btn').addEventListener('click', async () => {
  const idx = state.panelIdx;
  if (idx === null) return;
  const { listing } = state.jobs[idx];
  const btn = el('panel-save-btn');
  btn.disabled = true;
  btn.textContent = 'Saving…';
  try {
    await postJSON('/api/applications', {
      job_title: listing.title,
      company:   listing.company,
      job_url:   listing.url,
      source:    listing.source,
    });
    btn.textContent = 'Saved ✓';
    await loadTracker();
  } catch (err) {
    btn.disabled = false;
    btn.textContent = 'Save to Tracker';
    alert(`Could not save: ${err.message}`);
  }
});

// ─── Tracker ──────────────────────────────────────────────────────────────────
const STATUS_OPTIONS = [
  ['saved', 'Saved'],
  ['applied', 'Applied'],
  ['phone_screen', 'Phone Screen'],
  ['interview', 'Interview'],
  ['offer', 'Offer'],
  ['rejected', 'Rejected'],
];

async function loadTracker() {
  try {
    const apps = await getJSON('/api/applications');
    renderTracker(apps);
  } catch (_) { /* silent */ }
}

function renderTracker(apps) {
  if (!apps.length) {
    show('tracker-empty');
    hide('tracker-table');
    return;
  }
  hide('tracker-empty');
  show('tracker-table');

  el('tracker-body').innerHTML = apps.map(app => {
    const opts = STATUS_OPTIONS.map(([val, label]) =>
      `<option value="${val}" ${app.status === val ? 'selected' : ''}>${label}</option>`
    ).join('');
    const date = new Date(app.created_at).toLocaleDateString();
    return `
      <tr>
        <td><a href="${escHtml(app.job_url)}" target="_blank" rel="noopener noreferrer">${escHtml(app.job_title)}</a></td>
        <td>${escHtml(app.company)}</td>
        <td>${escHtml(app.source || '—')}</td>
        <td><select class="status-select" data-id="${app.id}">${opts}</select></td>
        <td>${date}</td>
      </tr>`;
  }).join('');

  el('tracker-body').querySelectorAll('.status-select').forEach(sel => {
    sel.addEventListener('change', async () => {
      try {
        await postJSON(`/api/applications/${sel.dataset.id}/status`, {
          status: sel.value, notes: '',
        });
      } catch (err) {
        alert(`Update failed: ${err.message}`);
      }
    });
  });
}

el('refresh-tracker-btn').addEventListener('click', loadTracker);

// ─── Utilities ────────────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ─── Init ─────────────────────────────────────────────────────────────────────
loadTracker();
