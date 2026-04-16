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
    try {
        const resp = await fetch(`/api/timesheet/export?month=${month}`, {
            credentials: 'same-origin',
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${month}.txt`;
        a.click();
        URL.revokeObjectURL(url);
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
