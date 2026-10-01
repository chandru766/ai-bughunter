const API_BASE = "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
    const navLinks = document.querySelectorAll(".nav-links li");
    const views = document.querySelectorAll(".view");

    navLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            navLinks.forEach(l => l.classList.remove("active"));
            e.target.classList.add("active");
            
            const targetPage = e.target.getAttribute("data-page");
            views.forEach(v => v.classList.remove("active"));
            
            const targetView = document.getElementById(`${targetPage}-view`);
            if(targetView) {
                targetView.classList.add("active");
                loadDataForView(targetPage);
            }
        });
    });

    loadDataForView('dashboard');
    checkKillSwitchStatus();
});

async function loadDataForView(view) {
    if(view === 'dashboard') {
        fetchDashboardStats();
        fetchSystemStatus();
    } else if(view === 'programs') {
        fetchPrograms();
    } else if(view === 'testing') {
        fetchTestPlans();
    } else if(view === 'auth') {
        fetchAuthContexts();
    } else if(view === 'findings') {
        fetchFindings();
    } else if(view === 'chains') {
        fetchChains();
    } else if(view === 'reports') {
        fetchReports();
    } else if(view === 'audit-logs') {
        fetchAuditLogs();
    }
}

// ==========================================
// Dashboard & System Status
// ==========================================
async function fetchDashboardStats() {
    try {
        const res = await fetch(`${API_BASE}/metrics`);
        const metrics = await res.json();
        
        const grid = document.getElementById('dashboard-stats');
        grid.innerHTML = `
            <div class="stat-card"><h3>EXECUTED</h3><div class="value success">${metrics.tests_executed}</div></div>
            <div class="stat-card"><h3>FAILED</h3><div class="value danger">${metrics.tests_failed}</div></div>
            <div class="stat-card"><h3>BLOCKED</h3><div class="value warning">${metrics.tests_blocked}</div></div>
            <div class="stat-card"><h3>FINDINGS</h3><div class="value" style="color:var(--accent-primary)">${metrics.findings_created}</div></div>
            <div class="stat-card"><h3>VALIDATED</h3><div class="value success">${metrics.findings_validated}</div></div>
            <div class="stat-card"><h3>REPORTS</h3><div class="value">${metrics.reports_generated}</div></div>
        `;
    } catch(e) {}
}

async function fetchSystemStatus() {
    try {
        const res = await fetch(`${API_BASE}/system/status`);
        const status = await res.json();
        
        const grid = document.getElementById('system-status-grid');
        grid.innerHTML = `
            <div class="stat-card"><h3>Backend API</h3><div class="value success" style="font-size:1.2rem">${status.backend}</div></div>
            <div class="stat-card"><h3>Database</h3><div class="value success" style="font-size:1.2rem">${status.database}</div></div>
            <div class="stat-card"><h3>AI Provider</h3><div class="value" style="color:var(--accent-primary); font-size:1.2rem">${status.ai_provider}</div></div>
            <div class="stat-card"><h3>RAG DB</h3><div class="value success" style="font-size:1.2rem">${status.rag}</div></div>
            <div class="stat-card"><h3>Kill Switch</h3><div class="value ${status.kill_switch ? 'danger' : 'success'}" style="font-size:1.2rem">${status.kill_switch ? 'ACTIVE' : 'INACTIVE'}</div></div>
            <div class="stat-card"><h3>Target Fixture</h3><div class="value success" style="font-size:1.2rem">${status.local_fixture}</div></div>
        `;
    } catch(e) {}
}

// ==========================================
// Programs
// ==========================================
async function fetchPrograms() {
    const res = await fetch(`${API_BASE}/programs`);
    const data = await res.json();
    const tbody = document.querySelector("#programs-table tbody");
    tbody.innerHTML = '';
    data.forEach(p => {
        tbody.innerHTML += `<tr>
            <td>${p.id}</td><td><strong>${p.name}</strong></td><td>${p.url}</td>
            <td><span class="badge validated">${p.status}</span></td>
        </tr>`;
    });
}

// ==========================================
// Kill Switch & Testing
// ==========================================
async function checkKillSwitchStatus() {
    try {
        const res = await fetch(`${API_BASE}/testing/kill-switch/status`);
        const data = await res.json();
        const ind = document.getElementById('global-status');
        const btn = document.getElementById('btn-killswitch');
        if(data.active) {
            ind.innerHTML = `<span class="dot" style="background:var(--accent-danger)"></span> TESTING HALTED`;
            ind.style.color = 'var(--accent-danger)';
            if(btn) btn.innerText = "🟢 RESUME TESTING";
        } else {
            ind.innerHTML = `<span class="dot green"></span> System Secure`;
            ind.style.color = 'inherit';
            if(btn) btn.innerText = "🔴 STOP ALL TESTING";
        }
    } catch (e) {}
}

async function toggleKillSwitch() {
    await fetch(`${API_BASE}/testing/kill-switch`, { method: 'POST' });
    checkKillSwitchStatus();
    if(document.getElementById('testing-view').classList.contains('active')) fetchTestPlans();
    if(document.getElementById('dashboard-view').classList.contains('active')) fetchSystemStatus();
}

// ==========================================
// Auth Bank
// ==========================================
async function addAuthContext() {
    const name = document.getElementById('auth-name').value;
    const label = document.getElementById('auth-label').value;
    const type = document.getElementById('auth-type').value;
    const secret = document.getElementById('auth-secret').value;
    
    if(!name || !secret) return alert("Name and Secret are required.");
    
    await fetch(`${API_BASE}/auth-bank/contexts`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ program_id: 1, name: name, account_label: label, auth_type: type, secret: secret })
    });
    fetchAuthContexts();
}

async function fetchAuthContexts() {
    const res = await fetch(`${API_BASE}/auth-bank/contexts`);
    const data = await res.json();
    const tbody = document.querySelector("#auth-table tbody");
    tbody.innerHTML = '';
    
    data.forEach(c => {
        tbody.innerHTML += `<tr>
            <td>${c.id}</td><td><strong>${c.name}</strong></td><td>${c.account_label}</td>
            <td><span class="badge" style="background:#3b82f644;color:#3b82f6">${c.auth_type}</span></td>
            <td style="font-family:monospace; color:var(--text-muted)">${c.secret}</td>
            <td><span class="badge validated">Configured</span></td>
        </tr>`;
    });
}

// ==========================================
// Testing
// ==========================================
async function planBolaTest() {
    const url = document.getElementById('bola-url').value;
    const src = document.getElementById('bola-source-id').value;
    const tgt = document.getElementById('bola-target-id').value;
    
    if(!url || !src || !tgt) return alert("Fill all BOLA fields.");
    
    const res = await fetch(`${API_BASE}/testing/bola?program_id=1&url=${encodeURIComponent(url)}&source_id=${src}&target_id=${tgt}`, { method: 'POST' });
    if(res.ok) fetchTestPlans();
    else alert("Failed to plan test.");
}

async function fetchTestPlans() {
    const res = await fetch(`${API_BASE}/testing/plans`);
    const data = await res.json();
    const tbody = document.querySelector("#plans-table tbody");
    tbody.innerHTML = '';
    
    data.forEach(p => {
        let actionBtn = "";
        if(p.status === 'PLANNED' && p.requires_human_approval) {
            actionBtn = `<button class="btn btn-validate" onclick="approveTest(${p.id})">Approve</button>`;
        } else if (p.status === 'APPROVED' || (!p.requires_human_approval && p.status === 'PLANNED')) {
            actionBtn = `<button class="btn" onclick="executeTest(${p.id})">Execute</button>`;
        }
        
        tbody.innerHTML += `<tr>
            <td>${p.id}</td><td>${p.test_category}</td><td>${p.url}</td>
            <td><span class="badge ${p.safety_level === 'APPROVAL_REQUIRED' ? 'unvalidated' : 'validated'}">${p.safety_level}</span></td>
            <td style="color:${p.status === 'BLOCKED' || p.status === 'FAILED' ? 'var(--accent-danger)' : 'inherit'}">${p.status}</td>
            <td>${actionBtn}</td>
        </tr>`;
    });
}

async function approveTest(id) {
    await fetch(`${API_BASE}/testing/approve/${id}`, { method: 'POST' });
    fetchTestPlans();
}

async function executeTest(id) {
    try {
        const res = await fetch(`${API_BASE}/testing/execute/${id}`, { method: 'POST' });
        const data = await res.json();
        if(res.ok) alert("Test Executed Successfully!");
        else alert("Execution Blocked: " + data.detail);
    } catch(e) {
        alert("Error executing test.");
    }
    fetchTestPlans();
}

// ==========================================
// Findings & Validation
// ==========================================
async function fetchFindings() {
    const res = await fetch(`${API_BASE}/findings`);
    const data = await res.json();
    const tbody = document.querySelector("#findings-table tbody");
    tbody.innerHTML = '';
    
    data.forEach(f => {
        let statusBadge = "unvalidated";
        if(f.status === "VALIDATED") statusBadge = "validated";
        if(f.status === "FALSE_POSITIVE") statusBadge = "rejected";
        
        tbody.innerHTML += `<tr>
            <td>${f.id}</td><td><strong>${f.title}</strong></td><td>${f.category}</td>
            <td style="color:var(--accent-warning)">${f.severity || 'N/A'}</td>
            <td><span class="badge ${statusBadge}">${f.status}</span></td>
            <td>${f.validation_status.replace('RESEARCHER_', '')}</td>
            <td><button class="btn" onclick="viewFinding(${f.id})">View / Validate</button></td>
        </tr>`;
    });
}

async function viewFinding(id) {
    const res = await fetch(`${API_BASE}/findings/${id}`);
    const f = await res.json();
    const modal = document.getElementById('finding-details-modal');
    
    let validationControls = "";
    if(f.status === "NEEDS_VALIDATION") {
        validationControls = `
            <div style="margin-top:20px; padding-top:20px; border-top:1px solid var(--border-color);">
                <h3>Human Validation</h3>
                <input type="text" id="validation-reason-${id}" placeholder="Validation reason (Required)" style="width:100%; padding:10px; background:var(--bg-dark); color:white; border:1px solid var(--border-color); margin-top:10px; margin-bottom:10px;">
                <button class="btn btn-validate" onclick="validateFinding(${id}, 'CONFIRM')">✅ CONFIRM FINDING</button>
                <button class="btn btn-reject" onclick="validateFinding(${id}, 'REJECT')">❌ REJECT / FALSE POSITIVE</button>
            </div>
        `;
    } else if (f.status === "VALIDATED") {
        validationControls = `
            <div style="margin-top:20px; padding-top:20px; border-top:1px solid var(--border-color);">
                <button class="btn" onclick="generateReport(${id})" style="width:100%; font-size:1.1rem; padding:10px;">📝 GENERATE SECURITY REPORT</button>
            </div>
        `;
    }
    
    modal.innerHTML = `
        <div style="display:flex; justify-content:space-between;">
            <h2 style="color:var(--accent-primary)">Finding #${f.id} - ${f.title}</h2>
            <button class="btn" style="background:transparent; border:1px solid var(--border-color);" onclick="document.getElementById('finding-details-modal').style.display='none'">Close</button>
        </div>
        <p style="margin-top:10px"><strong>Category:</strong> ${f.category} &nbsp; | &nbsp; <strong>Severity:</strong> <span style="color:var(--accent-warning)">${f.severity}</span></p>
        <p><strong>Status:</strong> ${f.status} &nbsp; | &nbsp; <strong>Validation:</strong> ${f.validation_status}</p>
        ${validationControls}
    `;
    modal.style.display = 'block';
}

async function validateFinding(id, decision) {
    const reason = document.getElementById(`validation-reason-${id}`).value;
    if(!reason) return alert("Validation reason is required.");
    
    const res = await fetch(`${API_BASE}/findings/${id}/validate`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ decision: decision, reason: reason })
    });
    
    if(res.ok) {
        document.getElementById('finding-details-modal').style.display = 'none';
        fetchFindings();
    } else {
        const data = await res.json();
        alert("Validation Failed: " + data.detail);
    }
}

// ==========================================
// Finding Chains
// ==========================================
async function fetchChains() {
    const res = await fetch(`${API_BASE}/finding-chains`);
    const data = await res.json();
    const tbody = document.querySelector("#chains-table tbody");
    tbody.innerHTML = '';
    data.forEach(c => {
        tbody.innerHTML += `<tr>
            <td>${c.id}</td>
            <td>Finding IDs: ${c.findings.join(', ')}</td>
            <td>${c.combined_impact}</td>
            <td><span class="badge unvalidated">${c.validation_status}</span></td>
        </tr>`;
    });
}

// ==========================================
// Reports
// ==========================================
async function generateReport(finding_id) {
    try {
        const res = await fetch(`${API_BASE}/reports/generate/${finding_id}`, { method: 'POST' });
        const data = await res.json();
        if(res.ok) {
            alert("Draft Report Generated successfully!");
            document.getElementById('finding-details-modal').style.display = 'none';
            document.querySelector('[data-page="reports"]').click();
        } else {
            alert("Report Generation Failed: " + data.detail);
        }
    } catch(e) {
        alert("Error generating report.");
    }
}

async function fetchReports() {
    const res = await fetch(`${API_BASE}/reports`);
    const data = await res.json();
    const tbody = document.querySelector("#reports-table tbody");
    tbody.innerHTML = '';
    data.forEach(r => {
        tbody.innerHTML += `<tr>
            <td>${r.id}</td>
            <td><a href="#" onclick="document.querySelector('[data-page=\\'findings\\']').click(); return false;">${r.finding_id}</a></td>
            <td>${new Date(r.created_at).toLocaleString()}</td>
            <td><button class="btn" onclick="viewReport(${r.id})">View Draft</button></td>
        </tr>`;
    });
}

async function viewReport(id) {
    const res = await fetch(`${API_BASE}/reports/${id}`);
    const r = await res.json();
    const modal = document.getElementById('report-details-modal');
    
    modal.innerHTML = `
        <div style="display:flex; justify-content:space-between;">
            <h2 style="color:var(--accent-warning)">⚠️ DRAFT SECURITY REPORT</h2>
            <button class="btn" style="background:transparent; border:1px solid var(--border-color);" onclick="document.getElementById('report-details-modal').style.display='none'">Close</button>
        </div>
        <div style="margin-top:10px; background:var(--bg-panel); padding:20px; border-radius:8px;">
            <pre style="white-space:pre-wrap; font-family:monospace; color:var(--text-main); font-size:0.9rem;">${r.markdown_content}</pre>
        </div>
        <div style="margin-top:20px; display:flex; gap:10px;">
            <button class="btn" onclick="alert('Markdown copied to clipboard (Simulated).')">Copy Markdown</button>
            <button class="btn" onclick="alert('JSON Export downloaded (Simulated).')">Download JSON</button>
        </div>
    `;
    modal.style.display = 'block';
}

// ==========================================
// Audit Logs
// ==========================================
async function fetchAuditLogs(page = 1) {
    try {
        const res = await fetch(`${API_BASE}/audit-logs?page=${page}&limit=50`);
        const logs = await res.json();
        const tbody = document.querySelector("#audit-table tbody");
        if(tbody) {
            tbody.innerHTML = '';
            logs.forEach(log => {
                let sevClass = '';
                if(log.severity === 'WARNING' || log.severity === 30) sevClass = 'warning';
                else if(log.severity === 'ERROR' || log.severity === 40) sevClass = 'danger';
                else sevClass = 'success';
                
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${new Date(log.timestamp).toLocaleString()}</td>
                    <td><span class="badge ${sevClass}">${log.severity}</span></td>
                    <td><strong>${log.action}</strong></td>
                    <td>${log.object}</td>
                    <td>${log.result}</td>
                    <td style="font-family:monospace; font-size:0.8rem; color:var(--text-muted)">${log.request_id || 'N/A'}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {}
}

// --- PHASE 19: RESEARCH ORCHESTRATION ---
async function loadResearchSessions() {
    try {
        const res = await fetch("http://127.0.0.1:9000/research/sessions");
        const data = await res.json();
        const tbody = document.querySelector("#sessions-table tbody");
        if(tbody) {
            tbody.innerHTML = "";
            data.forEach(s => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${s.id}</td>
                    <td>${s.program_id}</td>
                    <td>${s.name}</td>
                    <td><span class="badge status-${s.status.toLowerCase()}">${s.status}</span></td>
                    <td>
                        <button class="btn btn-sm" onclick="viewSessionCoverage(${s.id})">Coverage</button>
                        <button class="btn btn-sm" onclick="generateRecommendation(${s.id})">Recommend</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {}
}

async function createResearchSession() {
    const pid = document.getElementById("research-program-id").value;
    const name = document.getElementById("research-session-name").value;
    if(!pid || !name) return alert("Program ID and Name required");
    try {
        const res = await fetch("http://127.0.0.1:9000/research/sessions", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({program_id: parseInt(pid), name: name})
        });
        if(res.ok) loadResearchSessions();
    } catch (e) {}
}

async function viewSessionCoverage(id) {
    try {
        const res = await fetch(`http://127.0.0.1:9000/research/sessions/${id}/coverage`);
        const data = await res.json();
        document.getElementById("res-tested").innerText = data.tested_endpoints;
        document.getElementById("res-untested").innerText = data.total_endpoints - data.tested_endpoints;
    } catch (e) {}
}

async function generateRecommendation(id) {
    const ep = prompt("Enter endpoint path to analyze (e.g. /api/users):");
    if(!ep) return;
    try {
        const res = await fetch(`http://127.0.0.1:9000/research/sessions/${id}/recommendations/generate`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({endpoint: ep})
        });
        const rec = await res.json();
        if(res.ok) alert("AI Recommendation Generated: " + rec.possible_test_categories.join(", "));
        else alert("Failed: " + JSON.stringify(rec));
    } catch (e) {}
}

// --- PHASE 20: AI SECURITY LAB ---
async function loadAITestCases() {
    try {
        const res = await fetch("http://127.0.0.1:9000/ai-security/testcases");
        const data = await res.json();
        const tbody = document.querySelector("#ai-testcases-table tbody");
        if(tbody) {
            tbody.innerHTML = "";
            data.forEach(t => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${t.id}</td>
                    <td>${t.test_name}</td>
                    <td><span class="badge status-unknown">${t.category}</span></td>
                    <td><span class="badge status-${t.status.toLowerCase()}">${t.status}</span></td>
                    <td>
                        <button class="btn btn-sm" onclick="planAITestCase(${t.id})">Create Test Plan</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {}
}

async function createAIApplication() {
    const pid = document.getElementById("ai-app-program-id").value;
    const name = document.getElementById("ai-app-name").value;
    const url = document.getElementById("ai-app-url").value;
    if(!pid || !name || !url) return alert("Required fields missing");
    try {
        const res = await fetch("http://127.0.0.1:9000/ai-security/applications", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({program_id: parseInt(pid), name: name, base_url: url, description: "Local Lab"})
        });
        if(res.ok) alert("App Added");
    } catch (e) {}
}

async function createAITestCase() {
    const app_id = document.getElementById("ai-tc-app-id").value;
    const name = document.getElementById("ai-tc-name").value;
    const cat = document.getElementById("ai-tc-category").value;
    if(!app_id || !name) return alert("Required fields missing");
    try {
        const res = await fetch("http://127.0.0.1:9000/ai-security/testcases", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({application_id: parseInt(app_id), category: cat, test_name: name, description: "Test"})
        });
        if(res.ok) loadAITestCases();
    } catch (e) {}
}

async function planAITestCase(id) {
    try {
        const res = await fetch(`http://127.0.0.1:9000/ai-security/testcases/${id}/plan`, {method: "POST"});
        if(res.ok) {
            alert("Test Plan Created! Go to Active Testing to approve it.");
            loadAITestCases();
        } else {
            alert("Failed to plan test case");
        }
    } catch (e) {}
}

// --- PHASE 21: AGENT SECURITY LAB ---
async function loadAgents() {
    try {
        const res = await fetch("http://127.0.0.1:9000/agent-security/agents");
        const data = await res.json();
        const tbody = document.querySelector("#agent-table tbody");
        if(tbody) {
            tbody.innerHTML = "";
            data.forEach(a => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${a.id}</td>
                    <td>${a.name}</td>
                    <td><span class="badge status-${a.status.toLowerCase()}">${a.status}</span></td>
                    <td>${a.program_id}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {}
}

async function createAgent() {
    const appId = document.getElementById("agent-app-id").value;
    const progId = document.getElementById("agent-program-id").value;
    const name = document.getElementById("agent-name").value;
    if(!appId || !progId || !name) return alert("Required fields missing");
    try {
        const res = await fetch("http://127.0.0.1:9000/agent-security/agents", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({application_id: parseInt(appId), program_id: parseInt(progId), name: name, description: "Local Lab Agent"})
        });
        if(res.ok) loadAgents();
    } catch (e) {}
}

async function createTool() {
    const agentId = document.getElementById("tool-agent-id").value;
    const name = document.getElementById("tool-name").value;
    const risk = document.getElementById("tool-risk").value;
    if(!agentId || !name) return alert("Required fields missing");
    try {
        const res = await fetch("http://127.0.0.1:9000/agent-security/tools", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({agent_id: parseInt(agentId), name: name, risk_level: risk, description: "Local Mock Tool", requires_approval: risk === "HIGH_IMPACT"})
        });
        if(res.ok) alert("Tool Added");
    } catch (e) {}
}

// --- PHASE 22: MULTI-AGENT LAB ---
async function loadMultiAgentData() {
    try {
        const msgsRes = await fetch("http://127.0.0.1:9000/multi-agent/messages");
        const msgs = await msgsRes.json();
        const msgTbody = document.querySelector("#messages-table tbody");
        if(msgTbody) {
            msgTbody.innerHTML = "";
            msgs.forEach(m => {
                const tr = document.createElement("tr");
                tr.innerHTML = `<td>${m.id.substring(0,8)}...</td><td>${m.sender_id}</td><td>${m.receiver_id}</td><td>${m.type}</td><td><span class="badge status-${m.status.toLowerCase()}">${m.status}</span></td>`;
                msgTbody.appendChild(tr);
            });
        }
        
        const tasksRes = await fetch("http://127.0.0.1:9000/multi-agent/tasks");
        const tasks = await tasksRes.json();
        const taskTbody = document.querySelector("#tasks-table tbody");
        if(taskTbody) {
            taskTbody.innerHTML = "";
            tasks.forEach(t => {
                const tr = document.createElement("tr");
                tr.innerHTML = `<td>${t.id}</td><td>${t.agent_id}</td><td>${t.type}</td><td><span class="badge status-${t.status.toLowerCase()}">${t.status}</span></td>`;
                taskTbody.appendChild(tr);
            });
        }
    } catch (e) {}
}

async function createCapability() {
    const aid = document.getElementById("cap-agent-id").value;
    const name = document.getElementById("cap-name").value;
    const resType = document.getElementById("cap-resource").value;
    if(!aid || !name) return alert("Required fields missing");
    try {
        const res = await fetch("http://127.0.0.1:9000/multi-agent/capabilities", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({agent_id: parseInt(aid), capability_name: name, resource_type: resType, allowed_actions: "ALL"})
        });
        if(res.ok) {
            alert("Capability Added");
            loadMultiAgentData();
        }
    } catch (e) {}
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".nav-links li").forEach(li => {
        li.addEventListener("click", () => {
            const page = li.getAttribute("data-page");
            if(page === "research") loadResearchSessions();
            if(page === "ai-security") loadAITestCases();
            if(page === "agent-security") loadAgents();
            if(page === "multi-agent") loadMultiAgentData();
        });
    });
});
