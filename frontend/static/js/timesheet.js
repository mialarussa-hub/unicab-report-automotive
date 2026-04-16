// UNICAB — Timesheet Management

const CATEGORIES = {
    development: { label: 'Sviluppo', color: '#1a56db' },
    research: { label: 'Ricerca', color: '#7c3aed' },
    meeting: { label: 'Riunione', color: '#e67e22' },
    documentation: { label: 'Documentazione', color: '#27ae60' },
    deployment: { label: 'Deploy', color: '#e94560' },
};

function getCurrentMonth() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function getSelectedMonth() {
    return document.getElementById('month-picker').value || getCurrentMonth();
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    const picker = document.getElementById('month-picker');
    picker.value = getCurrentMonth();
    picker.addEventListener('change', () => {
        loadActivities();
        loadSummary();
    });

    // Set default date to today for the add form
    document.getElementById('act-date').valueAsDate = new Date();

    loadActivities();
    loadSummary();
});

// Add activity form
document.getElementById('activity-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('add-btn');
    btn.disabled = true;

    const data = {
        activity_date: document.getElementById('act-date').value,
        description: document.getElementById('act-desc').value.trim(),
        hours: parseFloat(document.getElementById('act-hours').value),
        category: document.getElementById('act-category').value,
        notes: document.getElementById('act-notes').value.trim() || null,
    };

    try {
        const resp = await fetch('/api/timesheet/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(data),
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }

        // Reset form (keep date and category)
        document.getElementById('act-desc').value = '';
        document.getElementById('act-hours').value = '';
        document.getElementById('act-notes').value = '';

        await Promise.all([loadActivities(), loadSummary()]);
    } catch (err) {
        alert('Errore: ' + err.message);
    } finally {
        btn.disabled = false;
    }
});

// Edit form
document.getElementById('edit-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('edit-id').value;

    const data = {
        activity_date: document.getElementById('edit-date').value,
        description: document.getElementById('edit-desc').value.trim(),
        hours: parseFloat(document.getElementById('edit-hours').value),
        category: document.getElementById('edit-category').value,
        notes: document.getElementById('edit-notes').value.trim() || null,
    };

    try {
        const resp = await fetch(`/api/timesheet/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(data),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        closeEditModal();
        await Promise.all([loadActivities(), loadSummary()]);
    } catch (err) {
        alert('Errore: ' + err.message);
    }
});

async function loadActivities() {
    const container = document.getElementById('activities-list');
    const month = getSelectedMonth();

    try {
        const resp = await fetch(`/api/timesheet/?month=${month}`, {
            credentials: 'same-origin',
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const activities = await resp.json();

        if (activities.length === 0) {
            container.innerHTML = '<p class="empty-state">Nessuna attivita registrata per questo mese.</p>';
            return;
        }

        container.innerHTML = '';
        for (const act of activities) {
            container.appendChild(createActivityCard(act));
        }
    } catch (err) {
        container.innerHTML = `<div class="error-banner">Errore caricamento: ${err.message}</div>`;
    }
}

async function loadSummary() {
    const month = getSelectedMonth();

    try {
        const resp = await fetch(`/api/timesheet/summary?month=${month}`, {
            credentials: 'same-origin',
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const summary = await resp.json();

        document.getElementById('total-hours').textContent = summary.total_hours + 'h';
        document.getElementById('total-count').textContent = summary.activity_count;

        // Category breakdown
        const breakdown = document.getElementById('category-breakdown');
        if (Object.keys(summary.by_category).length === 0) {
            breakdown.innerHTML = '<span class="empty-state">—</span>';
            return;
        }

        let html = '<div class="category-bars">';
        for (const [cat, hours] of Object.entries(summary.by_category)) {
            const info = CATEGORIES[cat] || { label: cat, color: '#999' };
            const pct = summary.total_hours > 0 ? (hours / summary.total_hours * 100) : 0;
            html += `
                <div class="category-bar-row">
                    <span class="category-bar-label" style="color:${info.color}">${info.label}</span>
                    <div class="category-bar-track">
                        <div class="category-bar-fill" style="width:${pct}%;background:${info.color}"></div>
                    </div>
                    <span class="category-bar-value">${hours}h</span>
                </div>
            `;
        }
        html += '</div>';
        breakdown.innerHTML = html;
    } catch (err) {
        document.getElementById('total-hours').textContent = '—';
        document.getElementById('total-count').textContent = '—';
        document.getElementById('category-breakdown').innerHTML = '';
    }
}

function createActivityCard(act) {
    const info = CATEGORIES[act.category] || { label: act.category, color: '#999' };
    const dateStr = new Date(act.activity_date).toLocaleDateString('it-IT', {
        weekday: 'short', day: '2-digit', month: 'short',
    });

    const card = document.createElement('div');
    card.className = 'activity-entry';
    card.innerHTML = `
        <div class="activity-left">
            <span class="activity-date">${dateStr}</span>
            <span class="category-badge" style="background:${info.color}15;color:${info.color};border:1px solid ${info.color}40">${info.label}</span>
        </div>
        <div class="activity-center">
            <div class="activity-desc">${escapeHtml(act.description)}</div>
            ${act.notes ? `<div class="activity-notes">${escapeHtml(act.notes)}</div>` : ''}
        </div>
        <div class="activity-right">
            <span class="activity-hours">${act.hours}h</span>
            <div class="activity-actions">
                <button class="btn-edit" onclick='openEditModal(${JSON.stringify(act)})'>Modifica</button>
                <button class="btn-delete" onclick="deleteActivity('${act.id}')">✕</button>
            </div>
        </div>
    `;
    return card;
}

function openEditModal(act) {
    document.getElementById('edit-id').value = act.id;
    document.getElementById('edit-date').value = act.activity_date;
    document.getElementById('edit-desc').value = act.description;
    document.getElementById('edit-hours').value = act.hours;
    document.getElementById('edit-category').value = act.category;
    document.getElementById('edit-notes').value = act.notes || '';
    document.getElementById('edit-modal').style.display = 'flex';
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function deleteActivity(id) {
    if (!confirm('Eliminare questa attivita?')) return;

    try {
        const resp = await fetch(`/api/timesheet/${id}`, {
            method: 'DELETE',
            credentials: 'same-origin',
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        await Promise.all([loadActivities(), loadSummary()]);
    } catch (err) {
        alert('Errore: ' + err.message);
    }
}

async function exportMonth() {
    const month = getSelectedMonth();
    const [y, m] = month.split('-');
    const monthLabel = new Date(y, m - 1).toLocaleDateString('it-IT', { month: 'long', year: 'numeric' });

    try {
        const [actResp, sumResp] = await Promise.all([
            fetch(`/api/timesheet/?month=${month}`, { credentials: 'same-origin' }),
            fetch(`/api/timesheet/summary?month=${month}`, { credentials: 'same-origin' }),
        ]);
        if (!actResp.ok || !sumResp.ok) throw new Error('Errore caricamento dati');
        const activities = await actResp.json();
        const summary = await sumResp.json();

        // Group by date
        const byDate = {};
        for (const act of activities) {
            const d = act.activity_date;
            if (!byDate[d]) byDate[d] = [];
            byDate[d].push(act);
        }
        const sortedDates = Object.keys(byDate).sort();

        // Build activity rows
        let rowsHtml = '';
        for (const date of sortedDates) {
            const dateStr = new Date(date).toLocaleDateString('it-IT', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' });
            const dayActivities = byDate[date];
            const dayHours = dayActivities.reduce((s, a) => s + a.hours, 0);

            for (let i = 0; i < dayActivities.length; i++) {
                const act = dayActivities[i];
                const info = CATEGORIES[act.category] || { label: act.category, color: '#999' };
                rowsHtml += `
                    <tr>
                        ${i === 0 ? `<td rowspan="${dayActivities.length}" style="font-weight:600;vertical-align:top;white-space:nowrap;border-right:1px solid #dee2e6">${dateStr}</td>` : ''}
                        <td>${escapeHtml(act.description)}${act.notes ? `<div style="font-size:0.8em;color:#888;margin-top:2px;font-style:italic">${escapeHtml(act.notes)}</div>` : ''}</td>
                        <td style="text-align:center"><span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:0.8em;font-weight:600;background:${info.color}18;color:${info.color};border:1px solid ${info.color}40">${info.label}</span></td>
                        <td style="text-align:right;font-weight:600;white-space:nowrap">${act.hours}h</td>
                    </tr>`;
            }
            rowsHtml += `
                <tr style="background:#f8f9fa;font-weight:600">
                    <td colspan="3" style="text-align:right;font-size:0.85em;color:#666">Subtotale giorno</td>
                    <td style="text-align:right;color:#e94560">${dayHours}h</td>
                </tr>`;
        }

        // Category summary bars
        let catHtml = '';
        for (const [cat, hours] of Object.entries(summary.by_category)) {
            const info = CATEGORIES[cat] || { label: cat, color: '#999' };
            const pct = summary.total_hours > 0 ? (hours / summary.total_hours * 100) : 0;
            catHtml += `
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                    <span style="width:110px;font-size:0.85em;font-weight:600;color:${info.color}">${info.label}</span>
                    <div style="flex:1;height:10px;background:#f0f0f0;border-radius:5px;overflow:hidden">
                        <div style="width:${pct}%;height:100%;background:${info.color};border-radius:5px"></div>
                    </div>
                    <span style="width:50px;text-align:right;font-size:0.85em;font-weight:600">${hours}h</span>
                    <span style="width:40px;text-align:right;font-size:0.75em;color:#999">${Math.round(pct)}%</span>
                </div>`;
        }

        const html = `<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>Report Attivita - ${monthLabel}</title>
<style>
    @page { margin: 15mm 12mm; size: A4; }
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #333; line-height: 1.5; padding: 20px; }
    .header { display:flex; justify-content:space-between; align-items:center; padding-bottom:16px; border-bottom:3px solid #1a1a2e; margin-bottom:24px; }
    .header h1 { font-size:1.4em; color:#1a1a2e; }
    .header .period { font-size:1.1em; color:#e94560; font-weight:600; text-transform:capitalize; }
    .summary { display:flex; gap:16px; margin-bottom:24px; }
    .sum-card { flex:1; background:#f8f9fa; border-radius:8px; padding:16px; text-align:center; border:1px solid #dee2e6; }
    .sum-card .label { font-size:0.75em; color:#888; text-transform:uppercase; letter-spacing:0.05em; }
    .sum-card .value { font-size:1.8em; font-weight:700; color:#1a1a2e; }
    .sum-card-wide { flex:2; text-align:left; }
    .section-title { font-size:1em; font-weight:700; color:#1a1a2e; margin-bottom:12px; padding-bottom:6px; border-bottom:1px solid #dee2e6; }
    table { width:100%; border-collapse:collapse; margin-bottom:24px; font-size:0.9em; }
    th { background:#1a1a2e; color:white; padding:8px 10px; text-align:left; font-size:0.85em; text-transform:uppercase; letter-spacing:0.03em; }
    td { padding:7px 10px; border-bottom:1px solid #eee; vertical-align:top; }
    tr:hover td { background:#fafafa; }
    .footer { margin-top:20px; padding-top:12px; border-top:2px solid #1a1a2e; display:flex; justify-content:space-between; font-size:0.8em; color:#888; }
    @media print {
        body { padding:0; }
        tr:hover td { background:transparent; }
    }
</style>
</head>
<body>
    <div class="header">
        <h1>UNICAB Report Automotive</h1>
        <div class="period">${monthLabel}</div>
    </div>

    <div class="summary">
        <div class="sum-card">
            <div class="label">Ore Totali</div>
            <div class="value">${summary.total_hours}h</div>
        </div>
        <div class="sum-card">
            <div class="label">Attivita</div>
            <div class="value">${summary.activity_count}</div>
        </div>
        <div class="sum-card">
            <div class="label">Giorni Lavorati</div>
            <div class="value">${sortedDates.length}</div>
        </div>
    </div>

    <div class="section-title">Distribuzione per Categoria</div>
    <div style="margin-bottom:24px">${catHtml}</div>

    <div class="section-title">Dettaglio Attivita</div>
    <table>
        <thead>
            <tr>
                <th style="width:180px">Data</th>
                <th>Descrizione</th>
                <th style="width:120px;text-align:center">Categoria</th>
                <th style="width:60px;text-align:right">Ore</th>
            </tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
        <tfoot>
            <tr style="background:#1a1a2e;color:white;font-weight:700">
                <td colspan="3" style="text-align:right;border:none;padding:10px">TOTALE</td>
                <td style="text-align:right;border:none;padding:10px;font-size:1.1em">${summary.total_hours}h</td>
            </tr>
        </tfoot>
    </table>

    <div class="footer">
        <span>UNICAB Italia S.r.l.</span>
        <span>Generato il ${new Date().toLocaleDateString('it-IT', { day:'2-digit', month:'long', year:'numeric' })}</span>
    </div>
</body>
</html>`;

        const win = window.open('', '_blank');
        win.document.write(html);
        win.document.close();
        win.onload = () => { win.print(); };
    } catch (err) {
        alert('Errore export: ' + err.message);
    }
}

// Close modal on overlay click
document.getElementById('edit-modal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeEditModal();
});

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
