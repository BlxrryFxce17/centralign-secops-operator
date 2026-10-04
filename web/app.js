// Security Operator Console
// Client Application & WebSocket Connection

let ws = null;
let currentTaskId = null;
let pendingApprovalReq = null;
let progressSimInterval = null;

const processStages = [
  { id: 'stage-understand', label: 'Find User Accounts', phase: 'UNDERSTANDING' },
  { id: 'stage-plan', label: 'Plan Actions', phase: 'PLANNING' },
  { id: 'stage-execute', label: 'Run Security Tools', phase: 'EXECUTING' },
  { id: 'stage-observe', label: 'Check Progress', phase: 'OBSERVING' },
  { id: 'stage-adapt', label: 'Fix Any Errors', phase: 'ADAPTING' },
  { id: 'stage-verify', label: 'Verify Success', phase: 'VERIFYING' },
  { id: 'stage-complete', label: 'Complete Task', phase: 'COMPLETED' }
];

// Initialize on DOM load
window.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('taskPrompt');
  if (input) {
    input.value = "Execute urgent security offboarding for employee Rahul Sharma (Data Platform Team). Revoke AWS IAM access keys, terminate active Google Workspace sessions, archive GitHub enterprise repo access, lock corporate laptop, and issue audit sign-off.";
  }
  connectWebSocket();
  fetchSecOpsData();
  fetchMemory();
});

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[CentrAlign Sentinel] Live telemetry stream connected.');
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'TRACE_EVENT') {
        handleTraceEvent(msg.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  ws.onclose = () => {
    setTimeout(connectWebSocket, 2000);
  };
}

function handleTraceEvent(data) {
  const event = data.event;
  addLogEntry(event);
  updatePipeline(event.phase);
  updateSplashFromEvent(event, data);

  if (data.plan && data.plan.length > 0) {
    renderSteps(data.plan);
  }

  if (event.phase === 'AWAITING_APPROVAL' && event.data) {
    showHITLAlert(event.data);
    showSplashHitl(event.data);
  } else if (event.phase === 'COMPLETED' || event.phase === 'FAILED') {
    hideHITLAlert();
    document.getElementById('runBtn').disabled = false;
    fetchSecOpsData();
    if (event.phase === 'COMPLETED') {
      showSplashCompletion(data);
    }
  }
}

/* ==========================================================================
   Splash Screen Controls
   ========================================================================== */
function openSplashScreen() {
  if (progressSimInterval) clearInterval(progressSimInterval);

  const overlay = document.getElementById('workflowSplash');
  const spinner = document.getElementById('splashSpinner');
  const title = document.getElementById('splashTitle');
  const subtitle = document.getElementById('splashSubtitle');
  const opMessage = document.getElementById('splashOpMessage');
  const opMeta = document.getElementById('splashOpMeta');
  const fill = document.getElementById('splashProgressFill');
  const pct = document.getElementById('splashPct');
  const hitlBox = document.getElementById('splashHitlPrompt');
  const footer = document.getElementById('splashCompletionFooter');
  const list = document.getElementById('splashProcessList');

  if (spinner) spinner.className = 'splash-spinner';
  if (fill) fill.style.width = '12%';
  if (pct) pct.innerText = '12%';
  if (title) title.innerText = 'Task In Progress';
  if (subtitle) subtitle.innerText = 'AI is working...';
  if (opMessage) opMessage.innerText = 'Starting up...';
  if (opMeta) opMeta.innerText = 'Phase: STARTING';
  if (hitlBox) hitlBox.classList.remove('visible');
  if (footer) footer.style.display = 'none';

  if (list) {
    list.innerHTML = processStages.map((s, idx) => `
      <div class="splash-process-item ${idx === 0 ? 'active' : ''}" id="${s.id}">
        <span class="item-icon ${idx === 0 ? 'active' : ''}">${idx === 0 ? '⟳' : '○'}</span>
        <span>${escapeHtml(s.label)}</span>
      </div>
    `).join('');
  }

  if (overlay) overlay.classList.add('visible');

  // Progressive simulated pacing
  let simPercent = 12;
  progressSimInterval = setInterval(() => {
    if (simPercent < 88) {
      simPercent += Math.floor(Math.random() * 4) + 1;
      if (simPercent > 88) simPercent = 88;
      if (fill) fill.style.width = simPercent + '%';
      if (pct) pct.innerText = simPercent + '%';
    }
  }, 350);
}

function updateSplashFromEvent(event) {
  const opMessage = document.getElementById('splashOpMessage');
  const opMeta = document.getElementById('splashOpMeta');
  const fill = document.getElementById('splashProgressFill');
  const pct = document.getElementById('splashPct');

  if (opMessage && event.message) {
    opMessage.innerText = event.message;
  }

  if (opMeta) {
    opMeta.innerText = `Phase: ${event.phase} • Target: Verified • Time: ${new Date().toLocaleTimeString()}`;
  }

  // Map phase to active progress stage
  const phaseOrder = ['UNDERSTANDING', 'PLANNING', 'EXECUTING', 'OBSERVING', 'ADAPTING', 'VERIFYING', 'COMPLETED'];
  const stageIdx = Math.max(0, phaseOrder.indexOf(event.phase));

  processStages.forEach((s, idx) => {
    const el = document.getElementById(s.id);
    if (!el) return;
    const icon = el.querySelector('.item-icon');
    if (idx < stageIdx) {
      el.className = 'splash-process-item completed';
      if (icon) { icon.className = 'item-icon completed'; icon.innerText = '✓'; }
    } else if (idx === stageIdx) {
      el.className = 'splash-process-item active';
      if (icon) { icon.className = 'item-icon active'; icon.innerText = '⟳'; }
    } else {
      el.className = 'splash-process-item';
      if (icon) { icon.className = 'item-icon'; icon.innerText = '○'; }
    }
  });

  const progressTargets = {
    'UNDERSTANDING': 22,
    'PLANNING': 38,
    'EXECUTING': 58,
    'OBSERVING': 72,
    'ADAPTING': 80,
    'VERIFYING': 92,
    'COMPLETED': 100
  };

  if (progressTargets[event.phase] !== undefined) {
    const target = progressTargets[event.phase];
    if (fill) fill.style.width = target + '%';
    if (pct) pct.innerText = target + '%';
  }
}

function showSplashHitl(alertData) {
  if (progressSimInterval) clearInterval(progressSimInterval);
  const hitlBox = document.getElementById('splashHitlPrompt');
  const body = document.getElementById('splashHitlBody');
  const spinner = document.getElementById('splashSpinner');

  if (spinner) spinner.className = 'splash-spinner paused';
  if (body) {
    body.innerHTML = `<strong>${escapeHtml(alertData.title || 'CISO Sign-Off Required')}</strong><br>${escapeHtml(alertData.reason || alertData.details || 'Target identity holds critical access privileges.')}`;
  }
  if (hitlBox) hitlBox.classList.add('visible');
}

function showSplashCompletion(data) {
  if (progressSimInterval) clearInterval(progressSimInterval);
  const fill = document.getElementById('splashProgressFill');
  const pct = document.getElementById('splashPct');
  const spinner = document.getElementById('splashSpinner');
  const title = document.getElementById('splashTitle');
  const hitlBox = document.getElementById('splashHitlPrompt');
  const footer = document.getElementById('splashCompletionFooter');
  const summary = document.getElementById('splashCompletionSummary');

  if (fill) fill.style.width = '100%';
  if (pct) pct.innerText = '100%';
  if (spinner) spinner.className = 'splash-spinner done';
  if (title) title.innerText = 'Access Revocation Verified & Sealed';
  if (hitlBox) hitlBox.classList.remove('visible');

  // Mark all steps completed
  processStages.forEach(s => {
    const el = document.getElementById(s.id);
    if (!el) return;
    el.className = 'splash-process-item completed';
    const icon = el.querySelector('.item-icon');
    if (icon) { icon.className = 'item-icon completed'; icon.innerText = '✓'; }
  });

  if (summary && data.summary) {
    summary.innerText = data.summary;
  }
  if (footer) footer.style.display = 'flex';
}

function closeSplashScreen() {
  const overlay = document.getElementById('workflowSplash');
  if (overlay) overlay.classList.remove('visible');
  switchTab('posture');
}

/* ==========================================================================
   HITL Gatekeeper Alerts
   ========================================================================== */
function showHITLAlert(data) {
  const alertEl = document.getElementById('hitlAlert');
  const titleEl = document.getElementById('hitlTitle');
  const descEl = document.getElementById('hitlDesc');

  if (titleEl) titleEl.innerText = data.title || 'CISO Authorization Required';
  if (descEl) descEl.innerText = data.reason || data.details || 'Target identity holds critical administrator tier access.';
  if (alertEl) alertEl.classList.add('visible');
}

function hideHITLAlert() {
  const alertEl = document.getElementById('hitlAlert');
  if (alertEl) alertEl.classList.remove('visible');
}

async function resolveHITL(approved) {
  const alertEl = document.getElementById('hitlAlert');
  if (alertEl) alertEl.classList.remove('visible');

  const splashHitl = document.getElementById('splashHitlPrompt');
  if (splashHitl) splashHitl.classList.remove('visible');

  const spinner = document.getElementById('splashSpinner');
  if (spinner) spinner.className = 'splash-spinner';

  if (!pendingApprovalReq) {
    console.error('No pending approval request found.');
    return;
  }

  try {
    const res = await fetch('/api/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_id: pendingApprovalReq.task_id,
        request_id: pendingApprovalReq.request_id,
        feedback: approved ? 'Approved by authorized CISO operator.' : 'Revocation halted by operator.'
      })
    });
    const result = await res.json();
    if (result.verification) {
      renderVerification(result.verification);
    }
    fetchSecOpsData();
  } catch (e) {
    console.error(e);
  }
}

/* ==========================================================================
   Task Execution Dispatch
   ========================================================================== */
async function executeTask() {
  const runBtn = document.getElementById('runBtn');
  const promptInput = document.getElementById('taskPrompt');
  const autoApproveToggle = document.getElementById('autoApproveToggle');

  const goal = promptInput.value.trim();
  if (!goal) return;

  runBtn.disabled = true;
  hideHITLAlert();
  resetPipeline();

  const auditStream = document.getElementById('auditStream');
  if (auditStream) auditStream.innerHTML = '';

  const stepStream = document.getElementById('stepStream');
  if (stepStream) {
    stepStream.innerHTML = `<div style="font-size: 12px; color: var(--text-tertiary); text-align: center; padding: 20px 0;">Decomposing objective into cognitive action sequence...</div>`;
  }

  openSplashScreen();

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal, auto_approve: autoApproveToggle.checked })
    });
    const data = await res.json();
    currentTaskId = data.task_id;
    document.getElementById('activeTaskId').innerText = data.task_id;

    if (progressSimInterval) clearInterval(progressSimInterval);

    if (data.plan) {
      renderSteps(data.plan);
    }

    if (data.verification) {
      renderVerification(data.verification);
    }

    if (data.status === 'AWAITING_APPROVAL' && data.pending_approvals && data.pending_approvals.length > 0) {
      const req = data.pending_approvals[0];
      pendingApprovalReq = req;
      showHITLAlert(req);
      showSplashHitl(req);
    } else if (data.status === 'COMPLETED') {
      showSplashCompletion(data);
      runBtn.disabled = false;
      fetchSecOpsData();
    } else if (data.status === 'FAILED') {
      runBtn.disabled = false;
      const opMsg = document.getElementById('splashOpMessage');
      if (opMsg) opMsg.innerText = 'Workflow failed: ' + (data.summary || 'Encountered error');
    }
  } catch (e) {
    if (progressSimInterval) clearInterval(progressSimInterval);
    console.error(e);
    runBtn.disabled = false;
  }
}

/* ==========================================================================
   Pipeline & Action Sequence Rendering
   ========================================================================== */
function resetPipeline() {
  document.querySelectorAll('.pipeline-bar .p-step').forEach(el => {
    el.classList.remove('active', 'completed');
  });
}

function updatePipeline(phase) {
  const stageMap = {
    'UNDERSTANDING': 'p-understand',
    'PLANNING': 'p-plan',
    'EXECUTING': 'p-execute',
    'OBSERVING': 'p-observe',
    'ADAPTING': 'p-adapt',
    'VERIFYING': 'p-verify',
    'COMPLETED': 'p-complete'
  };

  const currentId = stageMap[phase];
  if (!currentId) return;

  const order = ['p-understand', 'p-plan', 'p-execute', 'p-observe', 'p-adapt', 'p-verify', 'p-complete'];
  const curIdx = order.indexOf(currentId);

  order.forEach((id, idx) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (idx < curIdx) {
      el.className = 'p-step completed';
    } else if (idx === curIdx) {
      el.className = 'p-step active';
    } else {
      el.className = 'p-step';
    }
  });
}

function renderSteps(steps) {
  const container = document.getElementById('stepStream');
  if (!container) return;

  if (!steps || steps.length === 0) {
    container.innerHTML = `<div style="font-size: 12px; color: var(--text-tertiary); text-align: center; padding: 20px 0;">No steps defined.</div>`;
    return;
  }

  container.innerHTML = steps.map((s, idx) => {
    let statusClass = 'pending';
    let statusLabel = 'PENDING';
    if (s.status === 'RUNNING') { statusClass = 'running'; statusLabel = 'RUNNING'; }
    else if (s.status === 'SUCCESS') { statusClass = 'success'; statusLabel = 'SUCCESS'; }
    else if (s.status === 'FAILED') { statusClass = 'failed'; statusLabel = 'FAILED'; }
    else if (s.status === 'AWAITING_APPROVAL') { statusClass = 'awaiting'; statusLabel = 'AWAITING CISO'; }

    return `
      <div class="step-card ${statusClass}">
        <div class="step-card-header">
          <div class="step-card-title">
            <span class="step-num">${idx + 1}</span>
            <span>${escapeHtml(s.description)}</span>
          </div>
          <span class="step-status-tag ${statusClass}">${statusLabel}</span>
        </div>
        <div class="step-card-meta">
          <span>Tool: <code>${escapeHtml(s.tool_name)}</code></span>
          ${s.duration_ms ? `<span>Duration: ${Math.round(s.duration_ms)}ms</span>` : ''}
        </div>
        ${s.observation ? `
          <div class="step-card-obs">
            <strong>Observation:</strong> ${escapeHtml(s.observation)}
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

function renderVerification(v) {
  const container = document.getElementById('verifyChecklist');
  if (!container) return;

  if (!v || !v.details) {
    container.innerHTML = `<div style="font-size: 12px; color: var(--text-tertiary);">No verification results recorded yet.</div>`;
    return;
  }

  container.innerHTML = `
    <div style="font-size: 11.5px; font-weight: 650; color: ${v.verified ? 'var(--accent-green)' : 'var(--accent-red)'}; margin-bottom: 10px; padding: 8px 12px; border-radius: var(--radius-sm); background: ${v.verified ? 'var(--accent-green-subtle)' : 'var(--accent-red-subtle)'};">
      STATUS: ${v.verified ? 'ALL ZERO-PRIVILEGE INVARIANTS SATISFIED' : 'VERIFICATION FAILED'} (${v.assertions_passed}/${v.assertions_checked})
    </div>
    ${v.details.map(d => {
      const isPass = d.includes('[PASS]');
      const cleanText = d.replace('[PASS]', '').replace('[FAIL]', '').trim();
      return `
        <div class="assertion-item ${isPass ? 'passed' : 'failed'}">
          <span class="assertion-icon" style="color: ${isPass ? 'var(--accent-green)' : 'var(--accent-red)'};">${isPass ? '✓' : '✗'}</span>
          <div>${escapeHtml(cleanText)}</div>
        </div>
      `;
    }).join('')}
  `;
}

function addLogEntry(event) {
  const stream = document.getElementById('auditStream');
  if (!stream) return;

  const d = new Date(event.timestamp * 1000);
  const timeStr = d.toTimeString().split(' ')[0];

  const row = document.createElement('div');
  row.className = 'terminal-line';
  row.innerHTML = `
    <span class="terminal-time">[${timeStr}]</span>
    <span class="terminal-phase">[${event.phase}]</span>
    <span class="terminal-msg">${escapeHtml(event.message)}</span>
  `;
  stream.appendChild(row);
  stream.scrollTop = stream.scrollHeight;
}

function switchTab(name) {
  document.querySelectorAll('.tab-link').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(c => c.classList.remove('active'));

  const tabBtn = Array.from(document.querySelectorAll('.tab-link')).find(b => {
    const onclick = b.getAttribute('onclick');
    return onclick && onclick.includes(name);
  });
  if (tabBtn) tabBtn.classList.add('active');

  const target = document.getElementById(`tab-${name}`);
  if (target) target.classList.add('active');

  if (name === 'posture') fetchSecOpsData();
  if (name === 'policies') fetchMemory();
}

/* ==========================================================================
   SecOps Security Data Fetch & Posture Render
   ========================================================================== */
async function fetchSecOpsData() {
  try {
    const res = await fetch('/api/secops/data');
    const data = await res.json();

    // 1. Posture Summary Bar
    const summary = data.summary || {};
    const metricCloud = document.getElementById('metricCloudKeys');
    const metricSso = document.getElementById('metricSsoSessions');
    const metricDev = document.getElementById('metricUnlockedDevices');
    const statusText = document.getElementById('postureStatusText');

    if (metricCloud) metricCloud.innerText = summary.active_iam_keys ?? 0;
    if (metricSso) metricSso.innerText = summary.active_sso_sessions ?? 0;
    if (metricDev) metricDev.innerText = summary.unlocked_devices ?? 0;

    const totalActive = (summary.active_iam_keys || 0) + (summary.active_sso_sessions || 0);
    if (statusText) {
      statusText.innerText = (totalActive === 0 && (summary.unlocked_devices || 0) === 0)
        ? 'ZERO PRIVILEGE SECURED'
        : `${totalActive} ACTIVE CREDENTIALS`;
    }

    // 2. Incident Revocation Certificate Card
    const targetName = document.getElementById('revocationTargetName');
    const targetMeta = document.getElementById('revocationTargetMeta');
    const privCount = document.getElementById('activePrivilegesCount');
    const statusBadge = document.getElementById('revocationStatusBadge');
    const proofSso = document.getElementById('proofSsoText');
    const proofDevice = document.getElementById('proofDeviceText');

    const revokedEmp = (data.employees || []).find(e => ['REVOKED', 'OFFBOARDED', 'SUSPENDED'].includes(e.status)) || (data.employees || [])[0];
    if (revokedEmp) {
      const eName = revokedEmp.full_name || revokedEmp.name || 'Unknown';
      if (targetName) targetName.innerText = eName;
      if (targetMeta) targetMeta.innerText = `${revokedEmp.role} • ${revokedEmp.department} • ${revokedEmp.employee_id}`;
      
      const isRevoked = ['REVOKED', 'OFFBOARDED', 'SUSPENDED'].includes(revokedEmp.status);
      if (statusBadge) {
        statusBadge.innerText = isRevoked ? '✓ ZERO PRIVILEGES REMAINING' : '● ACTIVE PRIVILEGES ENROLLED';
        statusBadge.style.color = isRevoked ? '#34d399' : 'var(--accent-amber)';
        statusBadge.style.background = isRevoked ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.1)';
        statusBadge.style.borderColor = isRevoked ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)';
      }
      if (privCount) {
        privCount.innerText = isRevoked ? '0 ACTIVE' : '3 PRIVILEGED';
        privCount.style.color = isRevoked ? 'var(--accent-green)' : 'var(--accent-amber)';
      }
      if (proofSso) {
        proofSso.innerText = isRevoked ? 'SSO & Cloud Keys: REVOKED' : 'SSO & Cloud Keys: ACTIVE';
      }
      if (proofDevice) {
        proofDevice.innerText = isRevoked ? 'MDM Workstation: REMOTE_LOCKED' : 'MDM Workstation: ENROLLED';
      }
    }

    // 3. Render Employees Table
    renderEmployeesTable(data.employees || []);

    // 4. Render Active SSO Sessions Table
    renderSsoSessionsTable(data.sso_sessions || []);

    // 5. Render Cloud IAM Keys Table
    renderCloudKeysTable(data.cloud_keys || []);

    // 6. Render Source Code Repository Access Table
    renderRepoAccessTable(data.repo_access || []);

    // 7. Render Devices Table
    renderDevicesTable(data.devices || []);

  } catch (e) {
    console.error('[CentrAlign Sentinel] Error fetching SecOps data:', e);
  }
}

function renderEmployeesTable(employees) {
  const tbody = document.querySelector('#employeesTable tbody');
  if (!tbody) return;

  tbody.innerHTML = employees.map(emp => {
    const isRevoked = emp.status === 'REVOKED';
    const isCritical = emp.risk_tier === 'CRITICAL';
    const empName = emp.full_name || emp.name || 'Employee';
    return `
      <tr>
        <td>
          <div style="font-weight: 600; color: var(--text-primary);">${escapeHtml(empName)}</div>
          <div style="font-size: 10.5px; color: var(--text-tertiary); font-family: var(--font-mono);">${escapeHtml(emp.employee_id)}</div>
        </td>
        <td>
          <div>${escapeHtml(emp.role)}</div>
          <div style="font-size: 10.5px; color: var(--text-tertiary);">${escapeHtml(emp.department)}</div>
        </td>
        <td style="text-align: center;">
          <span class="badge ${isCritical ? 'amber' : 'green'}">${escapeHtml(emp.risk_tier)}</span>
        </td>
        <td style="text-align: center;">
          <span class="badge ${isRevoked ? 'green' : 'blue'}">${escapeHtml(emp.status)}</span>
        </td>
      </tr>
    `;
  }).join('');
}

function renderCloudKeysTable(keys) {
  const tbody = document.querySelector('#cloudKeysTable tbody');
  if (!tbody) return;

  tbody.innerHTML = keys.map(k => {
    const isRevoked = k.status === 'REVOKED';
    const prov = k.cloud_provider || k.provider || 'AWS';
    const isAws = prov.toUpperCase().includes('AWS');
    return `
      <tr>
        <td><span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-primary);">${escapeHtml(k.key_id)}</span></td>
        <td><span class="badge ${isAws ? 'amber' : 'blue'}">${escapeHtml(prov)}</span></td>
        <td>
          <div style="font-size: 12px;">${escapeHtml(k.permission_tier || k.iam_user_arn || 'AdministratorAccess')}</div>
          <div style="font-size: 10px; color: var(--text-tertiary);">${escapeHtml(k.employee_id)}</div>
        </td>
        <td style="text-align: center;">
          <span class="badge ${isRevoked ? 'green' : 'amber'}">${escapeHtml(k.status)}</span>
        </td>
      </tr>
    `;
  }).join('');
}

function renderSsoSessionsTable(sessions) {
  const tbody = document.querySelector('#ssoSessionsTable tbody');
  if (!tbody) return;

  tbody.innerHTML = sessions.map(s => {
    const isRevoked = s.status === 'REVOKED';
    const isOkta = (s.provider || '').toUpperCase().includes('OKTA');
    return `
      <tr>
        <td><span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-primary);">${escapeHtml(s.session_id)}</span></td>
        <td><span class="badge ${isOkta ? 'blue' : 'amber'}">${escapeHtml(s.provider)}</span></td>
        <td>
          <div style="font-size: 12px; font-family: var(--font-mono); color: var(--text-secondary);">${escapeHtml(s.ip_address)}</div>
          <div style="font-size: 10px; color: var(--text-tertiary);">${escapeHtml(s.employee_id)}</div>
        </td>
        <td style="text-align: center;">
          <span class="badge ${isRevoked ? 'green' : 'blue'}">${escapeHtml(s.status)}</span>
        </td>
      </tr>
    `;
  }).join('');
}

function renderRepoAccessTable(repos) {
  const tbody = document.querySelector('#repoAccessTable tbody');
  if (!tbody) return;

  tbody.innerHTML = repos.map(r => {
    const isRevoked = r.status === 'REVOKED';
    return `
      <tr>
        <td><span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-primary);">${escapeHtml(r.access_id)}</span></td>
        <td><span class="badge blue">${escapeHtml(r.platform)}</span></td>
        <td>
          <div style="font-size: 12px;">${escapeHtml(r.organization)} / ${escapeHtml(r.team_name)}</div>
          <div style="font-size: 10px; color: var(--text-tertiary);">${escapeHtml(r.employee_id)} • ${escapeHtml(r.permission)}</div>
        </td>
        <td style="text-align: center;">
          <span class="badge ${isRevoked ? 'green' : 'amber'}">${escapeHtml(r.status)}</span>
        </td>
      </tr>
    `;
  }).join('');
}

function renderDevicesTable(devices) {
  const tbody = document.querySelector('#devicesTable tbody');
  if (!tbody) return;

  tbody.innerHTML = devices.map(d => {
    const status = d.security_status || d.lock_status || 'ENROLLED';
    const isLocked = status === 'REMOTE_LOCKED';
    return `
      <tr>
        <td><span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-primary);">${escapeHtml(d.device_id)}</span></td>
        <td>
          <div>${escapeHtml(d.model || d.device_model)}</div>
          <div style="font-size: 10px; color: var(--text-tertiary); font-family: var(--font-mono);">SN: ${escapeHtml(d.serial_number)}</div>
        </td>
        <td><span style="font-size: 11px;">${escapeHtml(d.employee_id)}</span></td>
        <td style="text-align: center;">
          <span class="badge ${isLocked ? 'green' : 'blue'}">${escapeHtml(status)}</span>
        </td>
      </tr>
    `;
  }).join('');
}

async function resetSecOpsDB() {
  try {
    const res = await fetch('/api/secops/reset', { method: 'POST' });
    const data = await res.json();
    fetchSecOpsData();
    alert(data.status || 'Enterprise security database reset to seed state.');
  } catch (e) {
    console.error(e);
  }
}

async function fetchMemory() {
  try {
    const res = await fetch('/api/memory');
    const data = await res.json();
    const viewer = document.getElementById('policyViewer');
    if (viewer) {
      viewer.innerHTML = `<pre style="white-space: pre-wrap; margin: 0;">${escapeHtml(JSON.stringify(data.memory, null, 2))}</pre>`;
    }
  } catch (e) {
    console.error(e);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
