/**
 * Frontend JavaScript for AI-Powered Influencer Outreach Automation.
 * Handles API calls, dynamic rendering, approval queues, and interactive simulations.
 */

let currentTab = 'dashboard';
let currentCRMStatus = '';
let allInfluencersCache = [];

// --- Lifecycle & Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    refreshAllData();
    loadCampaignSettings();
});

function refreshAllData() {
    loadStats();
    loadCRMTable();
    loadAIEvaluationList();
    loadPendingEmails();
    loadDueFollowups();
    loadPendingReplies();
    populateReplySimulatorDropdown();
}

function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    const msgSpan = document.getElementById('toast-message');
    const iconSpan = document.getElementById('toast-icon');

    msgSpan.innerText = message;
    iconSpan.innerHTML = isError ? '<i class="fa-solid fa-triangle-exclamation text-rose-400"></i>' : '<i class="fa-solid fa-circle-check text-emerald-400"></i>';

    toast.classList.remove('translate-y-20', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');

    setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 3500);
}

// --- Navigation Tabs ---
function switchTab(tabName) {
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.nav-tab').forEach(el => {
        el.classList.remove('active-tab', 'border-blue-600', 'text-blue-600');
        el.classList.add('border-transparent', 'text-slate-500');
    });

    const activePane = document.getElementById(`tab-${tabName}`);
    const activeBtn = document.getElementById(`tab-btn-${tabName}`);

    if (activePane) activePane.classList.remove('hidden');
    if (activeBtn) {
        activeBtn.classList.add('active-tab', 'border-blue-600', 'text-blue-600');
        activeBtn.classList.remove('border-transparent', 'text-slate-500');
    }

    currentTab = tabName;
    refreshAllData();
}

// --- Dashboard & Metrics ---
async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();

        document.getElementById('kpi-total-leads').innerText = data.total_leads || 0;
        document.getElementById('kpi-emails-available').innerText = `${data.emails_available || 0} with verified business email`;
        document.getElementById('kpi-emails-sent').innerText = data.emails_sent || 0;
        document.getElementById('kpi-total-replies').innerText = data.total_replies || 0;
        document.getElementById('kpi-interested-count').innerText = `${data.interested_count || 0} interested / positive`;
        document.getElementById('kpi-confirmed').innerText = data.confirmed_count || 0;

        // Render pipeline badges
        const badgesContainer = document.getElementById('status-badges-container');
        badgesContainer.innerHTML = '';

        const statusConfigs = [
            { key: 'New Lead', label: 'New Lead', icon: 'fa-user-plus', color: 'slate' },
            { key: 'Email Available', label: 'Email Available', icon: 'fa-envelope-open-text', color: 'blue' },
            { key: 'Email Sent', label: 'Email Sent', icon: 'fa-paper-plane', color: 'indigo' },
            { key: 'Follow-up Due', label: 'Follow-up Due', icon: 'fa-clock', color: 'amber' },
            { key: 'Replied', label: 'Replied', icon: 'fa-reply', color: 'purple' },
            { key: 'Interested', label: 'Interested', icon: 'fa-thumbs-up', color: 'emerald' },
            { key: 'Not Interested', label: 'Not Interested', icon: 'fa-circle-xmark', color: 'rose' },
            { key: 'Collaboration Confirmed', label: 'Confirmed', icon: 'fa-handshake', color: 'emerald' }
        ];

        statusConfigs.forEach(st => {
            const count = data.status_breakdown[st.key] || 0;
            const badge = document.createElement('div');
            badge.className = `p-3 rounded-xl border bg-white shadow-sm flex flex-col items-center justify-center transition hover:shadow-md cursor-pointer`;
            badge.onclick = () => {
                switchTab('crm');
                filterCRMByStatus(st.key);
            };
            badge.innerHTML = `
                <div class="text-xs font-semibold text-slate-500 mb-1 flex items-center gap-1">
                    <i class="fa-solid ${st.icon} text-${st.color}-500"></i> ${st.label}
                </div>
                <div class="text-xl font-black text-slate-900">${count}</div>
            `;
            badgesContainer.appendChild(badge);
        });

    } catch (e) {
        console.error('Failed to load stats', e);
    }
}

// --- Step 1: Instagram Research ---
async function handleResearchSubmit(e) {
    if (e) e.preventDefault();
    const niche = document.getElementById('research-niche').value;
    const keywords = document.getElementById('research-keywords').value;
    const location = document.getElementById('research-location').value;
    const min_followers = parseInt(document.getElementById('research-min-followers').value) || 10000;
    const max_followers = parseInt(document.getElementById('research-max-followers').value) || 500000;
    const live_search = document.getElementById('research-live-search').checked;

    const btn = document.getElementById('btn-run-research');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/research', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ niche, keywords, location, min_followers, max_followers, live_search, save_to_crm: true })
        });
        const data = await res.json();

        document.getElementById('research-results-heading').innerText = `Discovered Creators (${data.found_count})`;
        document.getElementById('research-results-count').innerText = `${data.saved_to_crm} newly added to CRM`;

        renderResearchResults(data.results);
        showToast(`Found ${data.found_count} relevant creators! ${data.saved_to_crm} saved to CRM.`);
        refreshAllData();
    } catch (err) {
        showToast('Research query failed: ' + err.message, true);
    } finally {
        btn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Search Influencers';
        btn.disabled = false;
    }
}

async function loadSeedCreatorsToCRM() {
    try {
        const res = await fetch('/api/research', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ niche: '', min_followers: 0, max_followers: 1000000, save_to_crm: true })
        });
        const data = await res.json();
        renderResearchResults(data.results);
        showToast(`Loaded ${data.found_count} seed creators into CRM.`);
        refreshAllData();
    } catch (e) {
        showToast('Failed to load seed leads', true);
    }
}

function renderResearchResults(creators) {
    const grid = document.getElementById('research-results-grid');
    grid.innerHTML = '';

    if (!creators || creators.length === 0) {
        grid.innerHTML = `<div class="col-span-3 text-center py-8 text-slate-400 text-xs">No creators matched your criteria. Try widening the follower range or removing keywords.</div>`;
        return;
    }

    creators.forEach(c => {
        const card = document.createElement('div');
        card.className = 'bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-blue-300 transition';
        card.innerHTML = `
            <div>
                <div class="flex items-start justify-between mb-2">
                    <div>
                        <h5 class="text-sm font-bold text-slate-900">${c.name}</h5>
                        <a href="${c.profile_link}" target="_blank" class="text-xs text-blue-600 hover:underline flex items-center gap-1">
                            <i class="fa-brands fa-instagram"></i> @${c.username}
                        </a>
                    </div>
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                        ${c.niche}
                    </span>
                </div>
                <p class="text-xs text-slate-600 line-clamp-2 my-2">${c.bio || 'Public creator profile'}</p>
                <div class="grid grid-cols-2 gap-2 text-[11px] text-slate-500 my-2">
                    <div><i class="fa-solid fa-users mr-1 text-slate-400"></i> ${Number(c.follower_count).toLocaleString()} followers</div>
                    <div><i class="fa-solid fa-chart-line mr-1 text-slate-400"></i> ${c.engagement_rate || 3.5}% ER</div>
                    <div><i class="fa-solid fa-location-dot mr-1 text-slate-400"></i> ${c.location || 'Worldwide'}</div>
                    <div class="truncate text-blue-700"><i class="fa-solid fa-envelope mr-1 text-slate-400"></i> ${c.email || 'Email in bio'}</div>
                </div>
            </div>
            <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span class="text-[10px] text-emerald-600 font-bold"><i class="fa-solid fa-check"></i> Verified Public Data</span>
                <button onclick="switchTab('filter')" class="text-xs text-blue-600 font-bold hover:underline">
                    Filter with Claude &rarr;
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}

// --- Step 2: Claude AI Filtering ---
async function loadAIEvaluationList() {
    const list = document.getElementById('ai-evaluation-list');
    list.innerHTML = '';

    const res = await fetch('/api/influencers');
    const influencers = await res.json();

    if (!influencers || influencers.length === 0) {
        list.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">No influencers in CRM yet. Run Step 1 to discover creators.</div>`;
        return;
    }

    influencers.forEach(inf => {
        const score = inf.suitability_score || 0;
        const priority = inf.priority || 'Medium';
        const priorityColors = {
            'High': 'bg-emerald-100 text-emerald-800 border-emerald-300',
            'Medium': 'bg-blue-100 text-blue-800 border-blue-300',
            'Low': 'bg-slate-100 text-slate-700 border-slate-300'
        };

        const card = document.createElement('div');
        card.className = 'bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:border-purple-300 transition space-y-3';
        card.innerHTML = `
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-full bg-purple-50 text-purple-700 font-bold flex items-center justify-center text-sm border border-purple-200">
                        ${score || '--'}
                    </div>
                    <div>
                        <h4 class="text-sm font-bold text-slate-900">${inf.name} <span class="text-slate-400 font-normal">(@${inf.username})</span></h4>
                        <span class="text-xs text-slate-500">${inf.niche} • ${Number(inf.follower_count).toLocaleString()} followers • ${inf.location || 'Global'}</span>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="px-2.5 py-1 text-xs font-bold rounded-full border ${priorityColors[priority] || 'bg-slate-100 text-slate-700'}">
                        Priority: ${priority}
                    </span>
                    <button onclick="evaluateSingleCreator(${inf.id})" class="text-xs bg-purple-50 hover:bg-purple-100 text-purple-700 font-bold px-3 py-1.5 rounded-lg border border-purple-200 transition">
                        <i class="fa-solid fa-wand-magic-sparkles mr-1"></i> Re-Evaluate
                    </button>
                    <button onclick="generateColdEmailForCreator(${inf.id})" class="text-xs bg-blue-600 hover:bg-blue-700 text-white font-bold px-3 py-1.5 rounded-lg shadow-sm transition">
                        <i class="fa-solid fa-paper-plane mr-1"></i> Draft Email
                    </button>
                </div>
            </div>

            <!-- Score Progress Bar -->
            <div>
                <div class="flex justify-between text-[11px] font-semibold text-slate-600 mb-1">
                    <span>Brand Suitability Score</span>
                    <span>${score}/100</span>
                </div>
                <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div class="bg-gradient-to-r from-purple-500 to-indigo-600 h-2 rounded-full" style="width: ${score}%"></div>
                </div>
            </div>

            <!-- AI Summary & Personalization Hooks -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-2 border-t border-slate-100">
                <div class="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <span class="font-bold text-slate-700 block mb-1"><i class="fa-solid fa-brain text-purple-600 mr-1"></i> Claude Executive Summary</span>
                    <p class="text-slate-600 leading-relaxed">${inf.profile_summary || 'Run Claude evaluation to generate profile analysis.'}</p>
                </div>
                <div class="bg-purple-50/50 p-3 rounded-lg border border-purple-200">
                    <span class="font-bold text-purple-900 block mb-1"><i class="fa-solid fa-quote-left text-purple-600 mr-1"></i> Extracted Outreach Hook</span>
                    <p class="text-purple-800 leading-relaxed">${inf.personalization_hooks || 'Run evaluation to identify authentic post hooks.'}</p>
                </div>
            </div>
        `;
        list.appendChild(card);
    });
}

async function evaluateSingleCreator(influencerId) {
    try {
        showToast('Running Claude AI evaluation...');
        const res = await fetch(`/api/influencers/evaluate/${influencerId}`, { method: 'POST' });
        const data = await res.json();
        showToast(`Evaluated! Suitability Score: ${data.evaluation.suitability_score}/100`);
        refreshAllData();
    } catch (e) {
        showToast('Failed to evaluate creator', true);
    }
}

async function evaluateAllInfluencers() {
    const btn = document.getElementById('btn-eval-all');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scoring All Creators...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/influencers/evaluate-all', { method: 'POST' });
        const data = await res.json();
        showToast(`Successfully evaluated all ${data.total_evaluated} influencers with Claude AI!`);
        refreshAllData();
    } catch (e) {
        showToast('Failed to evaluate all influencers', true);
    } finally {
        btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Run Claude AI Evaluation on All Leads';
        btn.disabled = false;
    }
}

// --- Step 3: Google Sheets & CRM ---
async function loadCRMTable() {
    const tbody = document.getElementById('crm-table-body');
    tbody.innerHTML = '';

    const url = currentCRMStatus ? `/api/influencers?status=${encodeURIComponent(currentCRMStatus)}` : '/api/influencers';
    const res = await fetch(url);
    const influencers = await res.json();
    allInfluencersCache = influencers;

    if (!influencers || influencers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-slate-400">No records found matching status "${currentCRMStatus || 'All'}".</td></tr>`;
        return;
    }

    influencers.forEach(inf => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50 transition';

        const statusClass = `badge-${(inf.status || 'new-lead').toLowerCase().replace(/\s+/g, '-')}`;

        tr.innerHTML = `
            <td class="px-4 py-3">
                <div class="font-bold text-slate-900">${inf.name}</div>
                <a href="${inf.profile_link}" target="_blank" class="text-slate-400 hover:text-blue-600">@${inf.username}</a>
            </td>
            <td class="px-4 py-3 text-slate-600">${inf.niche}</td>
            <td class="px-4 py-3 font-medium text-slate-800">${Number(inf.follower_count).toLocaleString()}</td>
            <td class="px-4 py-3">
                ${inf.email ? `<span class="text-blue-600 font-mono">${inf.email}</span>` : `<span class="text-slate-400 italic">None collected</span>`}
            </td>
            <td class="px-4 py-3">
                <span class="inline-flex items-center px-2 py-0.5 rounded font-bold text-[11px] ${inf.suitability_score >= 80 ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-700'}">
                    ${inf.suitability_score || 0}/100
                </span>
            </td>
            <td class="px-4 py-3">
                <span class="px-2.5 py-1 rounded-full text-[10px] font-bold ${statusClass}">
                    ${inf.status}
                </span>
            </td>
            <td class="px-4 py-3 text-right space-x-1">
                <button onclick="generateColdEmailForCreator(${inf.id})" class="text-blue-600 hover:text-blue-800 font-bold p-1" title="Draft Email">
                    <i class="fa-solid fa-paper-plane"></i>
                </button>
                <button onclick="evaluateSingleCreator(${inf.id})" class="text-purple-600 hover:text-purple-800 font-bold p-1" title="Score with Claude">
                    <i class="fa-solid fa-wand-magic-sparkles"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterCRMByStatus(status) {
    currentCRMStatus = status;
    document.querySelectorAll('.status-pill').forEach(b => {
        if ((!status && b.innerText === 'All Leads') || b.innerText === status) {
            b.classList.add('active', 'bg-slate-800', 'text-white');
            b.classList.remove('bg-slate-100', 'text-slate-700');
        } else {
            b.classList.remove('active', 'bg-slate-800', 'text-white');
            b.classList.add('bg-slate-100', 'text-slate-700');
        }
    });
    loadCRMTable();
}

async function syncGoogleSheets() {
    const btn = document.getElementById('btn-sync-sheets');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Syncing...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/sheets/sync', { method: 'POST' });
        const data = await res.json();
        showToast(data.message || 'Synced to Google Sheets & Exports generated!');
    } catch (e) {
        showToast('Google Sheets sync error: ' + e.message, true);
    } finally {
        btn.innerHTML = '<i class="fa-brands fa-google-drive"></i> Sync to Google Sheets';
        btn.disabled = false;
    }
}

// --- Step 4: AI Cold Email Outreach & Approvals ---
async function generateColdEmailForCreator(influencerId) {
    try {
        showToast('Drafting personalized email with Claude AI...');
        const res = await fetch(`/api/emails/generate/${influencerId}`, { method: 'POST' });
        const data = await res.json();
        showToast(`Cold email generated for ${data.influencer_name}! Switched to Approval Queue.`);
        switchTab('cold-email');
        loadPendingEmails();
    } catch (e) {
        showToast('Failed to generate cold email', true);
    }
}

async function batchGenerateColdEmails() {
    const btn = document.getElementById('btn-batch-generate');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/emails/batch-generate?min_score=60', { method: 'POST' });
        const data = await res.json();
        showToast(`Generated ${data.generated_count} personalized email drafts!`);
        loadPendingEmails();
    } catch (e) {
        showToast('Failed to batch generate emails', true);
    } finally {
        btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Batch Generate Drafts (Score ≥ 60)';
        btn.disabled = false;
    }
}

async function loadPendingEmails() {
    const queue = document.getElementById('email-approval-queue');
    queue.innerHTML = '';

    const res = await fetch('/api/emails/pending');
    const emails = await res.json();

    if (!emails || emails.length === 0) {
        queue.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">No outreach emails waiting for approval. Click "Batch Generate Drafts" or select creators from the CRM.</div>`;
        return;
    }

    emails.forEach(em => {
        const card = document.createElement('div');
        card.className = 'bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3';
        card.id = `email-card-${em.id}`;
        card.innerHTML = `
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
                <div>
                    <span class="text-xs font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                        ${em.email_type.toUpperCase()} OUTREACH DRAFT
                    </span>
                    <h4 class="text-sm font-bold text-slate-900 mt-1">Recipient: ${em.influencer_name} &lt;${em.recipient_email}&gt;</h4>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="approveAndSendEmail(${em.id})" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold py-1.5 px-3 rounded-lg transition shadow-sm flex items-center gap-1">
                        <i class="fa-solid fa-check"></i> Approve & Send
                    </button>
                    <button onclick="rejectEmail(${em.id})" class="bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold py-1.5 px-3 rounded-lg border border-rose-200 transition">
                        <i class="fa-solid fa-xmark"></i> Reject
                    </button>
                </div>
            </div>

            <div>
                <label class="block text-[11px] font-bold text-slate-500 mb-1">Subject Line (Editable)</label>
                <input type="text" id="email-subj-${em.id}" value="${em.subject.replace(/"/g, '&quot;')}" class="w-full text-xs px-3 py-2 bg-slate-50 rounded-lg border border-slate-300 font-semibold text-slate-800">
            </div>

            <div>
                <label class="block text-[11px] font-bold text-slate-500 mb-1">Email Body (CAN-SPAM Compliant & Editable)</label>
                <textarea id="email-body-${em.id}" rows="8" class="w-full text-xs p-3 bg-slate-50 rounded-lg border border-slate-300 font-mono text-slate-700 leading-relaxed">${em.body}</textarea>
            </div>
        `;
        queue.appendChild(card);
    });
}

async function approveAndSendEmail(emailId) {
    try {
        const subj = document.getElementById(`email-subj-${emailId}`).value;
        const body = document.getElementById(`email-body-${emailId}`).value;

        // Approve
        await fetch(`/api/emails/approve/${emailId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject: subj, body: body })
        });

        // Send
        const res = await fetch(`/api/emails/send/${emailId}`, { method: 'POST' });
        const data = await res.json();

        showToast(data.message || 'Outreach email sent successfully!');
        refreshAllData();
    } catch (e) {
        showToast('Error sending email: ' + e.message, true);
    }
}

async function rejectEmail(emailId) {
    try {
        await fetch(`/api/emails/reject/${emailId}`, { method: 'POST' });
        showToast('Draft rejected.');
        loadPendingEmails();
    } catch (e) {
        showToast('Error rejecting draft', true);
    }
}

async function batchApproveAndSendEmails() {
    const btn = document.getElementById('btn-batch-send');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending All...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/emails/batch-approve-and-send', { method: 'POST' });
        const data = await res.json();
        showToast(`Dispatched ${data.total_sent} emails with anti-spam throttles!`);
        refreshAllData();
    } catch (e) {
        showToast('Batch send failed: ' + e.message, true);
    } finally {
        btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Batch Approve & Send All';
        btn.disabled = false;
    }
}

// --- Step 5: Automated Follow-ups ---
async function loadDueFollowups() {
    const container = document.getElementById('followups-due-list');
    container.innerHTML = '';

    const res = await fetch('/api/followups/due');
    const data = await res.json();

    if (!data.influencers || data.influencers.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-slate-400 text-xs">
                No follow-ups due right now. (Follow-up 1 triggers after 3-5 days; Follow-up 2 after 5-7 days).<br>
                Use the <span class="font-bold text-amber-700">"Test Simulator: +3 Days / +5 Days"</span> buttons above to test immediate eligibility!
            </div>
        `;
        return;
    }

    data.influencers.forEach(inf => {
        const card = document.createElement('div');
        card.className = 'bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3';
        card.innerHTML = `
            <div>
                <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                        Follow-up #${inf.followup_stage} Due
                    </span>
                    <h4 class="text-sm font-bold text-slate-900">${inf.name} (@${inf.username})</h4>
                </div>
                <p class="text-xs text-slate-600 mt-1">${inf.reason} Waiting for reply.</p>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="draftAndQueueFollowup(${inf.influencer_id}, ${inf.followup_stage})" class="bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold py-1.5 px-3 rounded-lg shadow-sm transition">
                    <i class="fa-solid fa-wand-magic-sparkles mr-1"></i> Draft Follow-up #${inf.followup_stage}
                </button>
            </div>
        `;
        container.appendChild(card);
    });
}

async function draftAndQueueFollowup(influencerId, stage) {
    try {
        const res = await fetch(`/api/followups/draft/${influencerId}?stage=${stage}`, { method: 'POST' });
        const data = await res.json();
        showToast(`Follow-up #${stage} drafted for review in Approval Queue!`);
        switchTab('cold-email');
        loadPendingEmails();
    } catch (e) {
        showToast('Follow-up blocked or error: ' + e.message, true);
    }
}

async function fastForwardTimeline(days) {
    try {
        const res = await fetch('/api/followups/fast-forward', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ days })
        });
        const data = await res.json();
        showToast(data.message);
        refreshAllData();
    } catch (e) {
        showToast('Timeline fast forward error: ' + e.message, true);
    }
}

// --- Step 6: AI Reply Management ---
function populateReplySimulatorDropdown() {
    const select = document.getElementById('reply-sim-influencer');
    select.innerHTML = '';

    const candidates = allInfluencersCache.filter(i => i.status !== 'New Lead');
    const listToUse = candidates.length > 0 ? candidates : allInfluencersCache;

    listToUse.forEach(inf => {
        const opt = document.createElement('option');
        opt.value = inf.id;
        opt.innerText = `${inf.name} (@${inf.username}) - Status: ${inf.status}`;
        select.appendChild(opt);
    });

    if (listToUse.length > 0) {
        loadReplyScenario('interested');
    }
}

function loadReplyScenario(scenario) {
    const textarea = document.getElementById('reply-sim-body');
    const scenarios = {
        'interested': "Hi Sankar Partnerships team! Thanks for reaching out. I checked out your Morning Radiance blend and it looks super interesting—I'm currently obsessed with adaptogens. I'd love to test out a VIP kit! Where do I send my shipping address?",
        'pricing': "Hey! Thanks for the note. My audience loves clean wellness products. Could you let me know what your budget is for an Instagram Reel + 2 story slides? My standard reel rate is $400. Let me know if that fits!",
        'collab': "Hello! I would be open to collaborating. Could you send over your campaign deliverables guide and exclusivity terms? I can deliver 1 Reel and 3 Stories next month if terms match.",
        'decline': "Hi, thanks for reaching out. I'm currently fully booked with brand sponsorships for the next two quarters, so I'll have to pass on this. Please remove me from your outreach roster."
    };
    textarea.value = scenarios[scenario] || '';
}

async function submitSimulatedReply() {
    const influencerId = document.getElementById('reply-sim-influencer').value;
    const body = document.getElementById('reply-sim-body').value;
    const btn = document.getElementById('btn-submit-reply');

    if (!influencerId || !body) {
        showToast('Select an influencer and message text.', true);
        return;
    }

    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Classifying with Claude...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/replies/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ influencer_id: parseInt(influencerId), body: body })
        });
        const data = await res.json();
        showToast(data.message);
        refreshAllData();
    } catch (e) {
        showToast('Reply simulation failed: ' + e.message, true);
    } finally {
        btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Send & Classify with Claude AI';
        btn.disabled = false;
    }
}

async function loadPendingReplies() {
    const queue = document.getElementById('replies-approval-queue');
    queue.innerHTML = '';

    const res = await fetch('/api/replies/pending');
    const replies = await res.json();

    if (!replies || replies.length === 0) {
        queue.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">No replies in inbox yet. Use the Reply Simulator on the left to trigger test responses!</div>`;
        return;
    }

    replies.forEach(r => {
        const card = document.createElement('div');
        card.className = 'bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3';
        
        const badgeColors = {
            'Interested': 'bg-emerald-100 text-emerald-800 border-emerald-300',
            'Pricing Enquiries': 'bg-blue-100 text-blue-800 border-blue-300',
            'Collaboration Requests': 'bg-purple-100 text-purple-800 border-purple-300',
            'Not Interested': 'bg-rose-100 text-rose-800 border-rose-300'
        };

        card.innerHTML = `
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
                <div>
                    <div class="flex items-center gap-2">
                        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold border ${badgeColors[r.classification] || 'bg-slate-100 text-slate-700'}">
                            ${r.classification}
                        </span>
                        <span class="text-xs text-slate-500">Sentiment: <strong>${r.sentiment || 'Positive'}</strong></span>
                        <span class="text-xs text-slate-400">• CRM Updated to: <strong class="text-slate-700">${r.influencer_status}</strong></span>
                    </div>
                    <h4 class="text-sm font-bold text-slate-900 mt-1">From: ${r.influencer_name} &lt;${r.sender_email}&gt;</h4>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="approveReplyDraft(${r.id})" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold py-1.5 px-3 rounded-lg transition shadow-sm flex items-center gap-1">
                        <i class="fa-solid fa-paper-plane"></i> Approve & Send Reply
                    </button>
                </div>
            </div>

            <!-- Original Incoming Text -->
            <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs text-slate-700">
                <span class="font-bold text-slate-500 block text-[10px] uppercase mb-1">Incoming Influencer Message:</span>
                <p class="italic">"${r.body}"</p>
            </div>

            <!-- AI Suggested Next Action -->
            <div class="bg-indigo-50/50 p-2.5 rounded-lg border border-indigo-200 text-xs text-indigo-900 flex items-center gap-2">
                <i class="fa-solid fa-lightbulb text-indigo-600"></i>
                <span><strong>Suggested Next Action:</strong> ${r.next_action}</span>
            </div>

            <!-- AI Drafted Reply Body -->
            <div>
                <label class="block text-[11px] font-bold text-slate-500 mb-1">AI-Generated Reply Draft (Editable & Requires Human Approval)</label>
                <textarea id="reply-draft-text-${r.id}" rows="5" class="w-full text-xs p-3 bg-white rounded-lg border border-slate-300 font-mono text-slate-800 leading-relaxed">${r.reply_draft}</textarea>
            </div>
        `;
        queue.appendChild(card);
    });
}

async function approveReplyDraft(replyId) {
    try {
        const updated = document.getElementById(`reply-draft-text-${replyId}`).value;
        const res = await fetch(`/api/replies/approve/${replyId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ updated_draft: updated })
        });
        const data = await res.json();
        showToast(data.message || 'Approved reply sent!');
        refreshAllData();
    } catch (e) {
        showToast('Error approving reply', true);
    }
}

// --- Campaign Settings Modal ---
function openSettingsModal() {
    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.add('hidden');
}

async function loadCampaignSettings() {
    try {
        const res = await fetch('/api/campaign');
        const camp = await res.json();
        document.getElementById('cfg-brand-name').value = camp.brand_name || '';
        document.getElementById('cfg-brand-niche').value = camp.brand_niche || '';
        document.getElementById('cfg-product-name').value = camp.product_name || '';
        document.getElementById('cfg-product-desc').value = camp.product_description || '';
        document.getElementById('cfg-collab-type').value = camp.collaboration_type || '';
        document.getElementById('cfg-sender-name').value = camp.sender_name || '';
        document.getElementById('cfg-sender-title').value = camp.sender_title || '';
        document.getElementById('cfg-sender-email').value = camp.sender_email || '';
        document.getElementById('cfg-company-address').value = camp.company_address || '';
    } catch (e) {
        console.error('Failed to load campaign settings', e);
    }
}

async function saveCampaignSettings(e) {
    if (e) e.preventDefault();
    const payload = {
        brand_name: document.getElementById('cfg-brand-name').value,
        brand_niche: document.getElementById('cfg-brand-niche').value,
        product_name: document.getElementById('cfg-product-name').value,
        product_description: document.getElementById('cfg-product-desc').value,
        collaboration_type: document.getElementById('cfg-collab-type').value,
        sender_name: document.getElementById('cfg-sender-name').value,
        sender_title: document.getElementById('cfg-sender-title').value,
        sender_email: document.getElementById('cfg-sender-email').value,
        company_address: document.getElementById('cfg-company-address').value
    };

    try {
        await fetch('/api/campaign', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        showToast('Campaign settings saved successfully!');
        closeSettingsModal();
    } catch (err) {
        showToast('Failed to save settings', true);
    }
}
