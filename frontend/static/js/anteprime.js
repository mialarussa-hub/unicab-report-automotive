// UNICAB — Anteprime dashboard (read-only featured sessions)
// Lists sessions flagged via /scraping-test and lets any authenticated user
// (admin or client) browse them. Layout: accordion (all collapsed by default),
// each item lazy-loads its detail on first open.

async function loadFeaturedSessions() {
    const listEl = document.getElementById('featured-list');
    const emptyEl = document.getElementById('featured-empty');
    const loadingEl = document.getElementById('featured-loading');

    try {
        const resp = await fetch('/api/scraping-test/featured', { credentials: 'same-origin' });
        if (loadingEl) loadingEl.style.display = 'none';

        if (!resp.ok) {
            if (resp.status === 401) {
                window.location.href = '/frontend/login';
                return;
            }
            showError('Impossibile caricare le anteprime.');
            return;
        }

        const sessions = await resp.json();
        if (!sessions || sessions.length === 0) {
            if (emptyEl) emptyEl.style.display = 'block';
            return;
        }

        listEl.innerHTML = '';
        for (const s of sessions) {
            listEl.appendChild(buildSessionAccordion(s));
        }
    } catch (err) {
        console.error('Failed to load featured sessions:', err);
        if (loadingEl) loadingEl.style.display = 'none';
        showError('Errore di rete durante il caricamento.');
    }
}

function buildSessionAccordion(sessionSummary) {
    const det = document.createElement('details');
    det.className = 'featured-session';
    det.dataset.sessionId = sessionSummary.id;

    const date = sessionSummary.started_at ? new Date(sessionSummary.started_at) : null;
    const dateStr = date ? date.toLocaleDateString('it-IT', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    }) : '';

    const phase = sessionSummary.phase_filter || 'all';
    const phaseBadge = PHASE_BADGES[phase] || PHASE_BADGES.all;
    const motoreFilter = formatMotoreFilter(sessionSummary.filter_alimentazione, sessionSummary.filter_cilindrata);
    const motoreBadge = motoreFilter
        ? `<span class="motore-badge">${escapeHtml(motoreFilter)}</span>`
        : '';

    const summary = document.createElement('summary');
    summary.className = 'featured-summary';
    summary.innerHTML = `
        <span class="featured-caret">\u25B8</span>
        <div class="featured-title">
            <strong>${escapeHtml(sessionSummary.brand)}${sessionSummary.model ? ' ' + escapeHtml(sessionSummary.model) : ''}</strong>
            <span class="phase-badge ${phaseBadge.class}">${phaseBadge.label}</span>
            ${motoreBadge}
        </div>
        <div class="featured-meta">
            <span class="featured-date">${escapeHtml(dateStr)}</span>
            <span class="featured-stats">${sessionSummary.total_results ?? 0} risultati</span>
        </div>
    `;
    det.appendChild(summary);

    const body = document.createElement('div');
    body.className = 'featured-body';
    body.innerHTML = '<div class="featured-body-loading">Caricamento del dettaglio…</div>';
    det.appendChild(body);

    // Lazy load: fetch detail only on first expand
    let loaded = false;
    det.addEventListener('toggle', async () => {
        if (!det.open || loaded) return;
        loaded = true;
        try {
            const resp = await fetch(`/api/scraping-test/sessions/${sessionSummary.id}`, { credentials: 'same-origin' });
            if (!resp.ok) {
                body.innerHTML = `<div class="featured-error">Impossibile caricare il dettaglio (HTTP ${resp.status}).</div>`;
                return;
            }
            const data = await resp.json();
            body.innerHTML = '';
            renderResultsInto(body, data, /* fromSession */ true);
        } catch (err) {
            console.error('Detail fetch failed:', err);
            body.innerHTML = '<div class="featured-error">Errore di rete.</div>';
        }
    });

    return det;
}

function showError(msg) {
    const errEl = document.getElementById('featured-error');
    if (errEl) {
        errEl.textContent = msg;
        errEl.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', loadFeaturedSessions);
