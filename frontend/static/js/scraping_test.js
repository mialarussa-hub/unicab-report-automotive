// UNICAB — Scraping Test Frontend (with real-time progress tracking)

const TYPE_ICONS = {
    forum: '\uD83D\uDCAC',
    news: '\uD83D\uDCF0',
    youtube: '\u25B6\uFE0F',
    social: '\uD83D\uDC65',
    official: '\uD83C\uDFE2',
    perplexity: '\uD83E\uDDE0',
};

const STATUS_LABELS = {
    ok: { label: 'OK', class: 'status-ok' },
    partial: { label: 'Parziale', class: 'status-partial' },
    error: { label: 'Errore', class: 'status-error' },
};

const PHASE_BADGES = {
    all: { label: 'Tutte le fasi', class: 'phase-all' },
    L1: { label: 'L1 Ufficiale', class: 'phase-l1' },
    L2: { label: 'L2 Media', class: 'phase-l2' },
    L3: { label: 'L3 Utenti', class: 'phase-l3' },
};

const ALIMENTAZIONE_LABEL = {
    benzina: 'Benzina', diesel: 'Diesel', gpl: 'GPL', metano: 'Metano',
    elettrico: 'Elettrico',
    ibrido_full: 'Ibrido Full', ibrido_mild: 'Ibrido Mild', ibrido_plugin: 'Plug-in',
};

function formatMotoreFilter(alim, cil) {
    const parts = [];
    if (cil != null) parts.push(`${cil} L`);
    if (alim) parts.push(ALIMENTAZIONE_LABEL[alim] || alim);
    return parts.length ? parts.join(' · ') : null;
}

function buildMotoreFilterBanner(data) {
    const requested = formatMotoreFilter(data.filter_alimentazione, data.filter_cilindrata);
    if (!requested) return null;

    const effective = data.filter_effective || {};
    const perPhase = effective.per_phase || {};
    const phaseFilter = data.phase_filter || 'all';
    const phases = phaseFilter === 'all' ? ['L1', 'L2', 'L3'] : [phaseFilter];

    const rows = [];
    let anyDegraded = false;
    for (const p of phases) {
        const ph = perPhase[p];
        if (!ph) continue;
        const eff = formatMotoreFilter(ph.alimentazione, ph.cilindrata);
        const degraded = !!ph.degraded;
        if (degraded) anyDegraded = true;
        const eff_label = eff || 'nessun filtro (fallback)';
        const match_count = ph.matches || 0;
        const badge = PHASE_BADGES[p];
        rows.push(`
            <li class="motore-row ${degraded ? 'degraded' : ''}">
                <span class="phase-badge ${badge.class}">${badge.label}</span>
                <span class="motore-eff">${escapeHtml(eff_label)}</span>
                <span class="motore-matches">${match_count} match</span>
                ${degraded ? '<span class="motore-degraded-tag">filtro allentato</span>' : ''}
            </li>
        `);
    }

    const banner = document.createElement('div');
    banner.className = 'motore-banner' + (anyDegraded ? ' has-degraded' : '');
    banner.innerHTML = `
        <div class="motore-banner-header">
            <strong>Filtro motore richiesto:</strong>
            <span class="motore-requested">${escapeHtml(requested)}</span>
            <label class="motore-toggle">
                <input type="checkbox" id="show-non-matches">
                Mostra anche risultati non pertinenti
            </label>
        </div>
        ${rows.length ? `<ul class="motore-phases">${rows.join('')}</ul>` : ''}
    `;
    // Wire toggle to re-render
    setTimeout(() => {
        const toggle = document.getElementById('show-non-matches');
        if (toggle) {
            toggle.addEventListener('change', () => {
                document.body.classList.toggle('show-non-matches', toggle.checked);
            });
        }
    }, 0);
    return banner;
}

let activePollInterval = null;
let activeTimerInterval = null;
let scrapeStartTime = null;
let activeSessionId = null;

// Load previous sessions on page load
document.addEventListener('DOMContentLoaded', loadSessions);

document.getElementById('scraping-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const brand = document.getElementById('brand').value.trim();
    const model = document.getElementById('model').value.trim();
    const phase = document.getElementById('phase').value || 'all';
    const alimentazione = document.getElementById('alimentazione').value || null;
    const cilRaw = document.getElementById('cilindrata').value;
    const cilindrata = cilRaw ? parseFloat(cilRaw) : null;
    if (!brand) return;

    const submitBtn = document.getElementById('submit-btn');
    const resultsContainer = document.getElementById('results');
    const resultsMeta = document.getElementById('results-meta');

    // Reset
    submitBtn.disabled = true;
    resultsContainer.innerHTML = '';
    resultsMeta.style.display = 'none';
    stopPolling();

    try {
        const resp = await fetch('/api/scraping-test/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ brand, model, phase, alimentazione, cilindrata }),
        });

        if (!resp.ok) {
            let errMsg = `HTTP ${resp.status}`;
            try { const err = await resp.json(); if (err.detail) errMsg = err.detail; } catch {}
            throw new Error(errMsg);
        }
        const data = await resp.json();

        if (data.status === 'running' && data.session_id) {
            // Async mode — show progress and start polling
            scrapeStartTime = Date.now();
            activeSessionId = data.session_id;
            renderProgressCard(data.sources_names || [], brand, model, phase);
            startPolling(data.session_id);
        } else {
            // Legacy sync fallback
            renderResults(data);
            loadSessions();
            submitBtn.disabled = false;
        }

    } catch (err) {
        resultsContainer.innerHTML = `<div class="error-banner">Errore: ${err.message}</div>`;
        submitBtn.disabled = false;
    }
});


// ---------------------------------------------------------------------------
// Polling
// ---------------------------------------------------------------------------

function startPolling(sessionId) {
    activePollInterval = setInterval(async () => {
        try {
            const resp = await fetch(`/api/scraping-test/sessions/${sessionId}`, {
                credentials: 'same-origin',
            });
            if (!resp.ok) return;
            const data = await resp.json();

            // Update progress card with completed sources
            updateProgressCard(data);

            if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
                stopPolling();
                activeSessionId = null;
                if (data.status === 'cancelled') {
                    document.getElementById('results').innerHTML =
                        `<div class="cancel-banner">Sessione annullata.</div>`;
                } else {
                    renderResults(data, true);
                }
                loadSessions();
                document.getElementById('submit-btn').disabled = false;
            }
        } catch (err) {
            console.error('Poll error:', err);
        }
    }, 2500);

    // Elapsed time counter
    activeTimerInterval = setInterval(() => {
        const timerEl = document.getElementById('progress-timer');
        if (timerEl && scrapeStartTime) {
            const elapsed = Math.floor((Date.now() - scrapeStartTime) / 1000);
            timerEl.textContent = formatElapsed(elapsed);
        }
    }, 1000);
}

function stopPolling() {
    if (activePollInterval) {
        clearInterval(activePollInterval);
        activePollInterval = null;
    }
    if (activeTimerInterval) {
        clearInterval(activeTimerInterval);
        activeTimerInterval = null;
    }
}


// ---------------------------------------------------------------------------
// Progress Card (shown during scraping)
// ---------------------------------------------------------------------------

function renderProgressCard(sourceNames, brand, model, phase = 'all') {
    const container = document.getElementById('results');
    const label = `${brand}${model ? ' ' + model : ''}`;
    const phaseBadge = PHASE_BADGES[phase] || PHASE_BADGES.all;

    container.innerHTML = `
        <div class="progress-card">
            <div class="progress-header">
                <div class="progress-title">
                    <span class="spinner-inline"></span>
                    Scraping <strong>${escapeHtml(label)}</strong>
                    <span class="phase-badge ${phaseBadge.class}">${phaseBadge.label}</span>
                </div>
                <div class="progress-actions">
                    <div class="progress-timer" id="progress-timer">0:00</div>
                    <button type="button" id="cancel-scrape-btn" class="cancel-btn" title="Annulla scraping">
                        \u2715 Annulla
                    </button>
                </div>
            </div>
            <div class="progress-sources" id="progress-sources">
                ${sourceNames.map(name => `
                    <div class="progress-source" data-source="${escapeHtml(name)}">
                        <span class="progress-status-icon pending">\u23F3</span>
                        <span class="progress-source-name">${escapeHtml(name)}</span>
                        <span class="progress-source-detail">in attesa</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    const cancelBtn = document.getElementById('cancel-scrape-btn');
    if (cancelBtn) cancelBtn.addEventListener('click', cancelActiveScrape);
}

async function cancelActiveScrape() {
    if (!activeSessionId) return;
    const btn = document.getElementById('cancel-scrape-btn');
    if (!confirm('Annullare lo scraping in corso?\n\nLe chiamate gi\u00e0 partite non possono essere interrotte ma i risultati non verranno salvati.')) return;
    if (btn) { btn.disabled = true; btn.textContent = 'Annullamento...'; }

    try {
        const resp = await fetch(`/api/scraping-test/sessions/${activeSessionId}/cancel`, {
            method: 'POST',
            credentials: 'same-origin',
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    } catch (err) {
        console.error('Cancel error:', err);
        if (btn) { btn.disabled = false; btn.textContent = '\u2715 Annulla'; }
        alert('Errore durante l\'annullamento: ' + err.message);
        return;
    }

    stopPolling();
    const cancelledId = activeSessionId;
    activeSessionId = null;
    document.getElementById('results').innerHTML =
        `<div class="cancel-banner">Sessione annullata. I risultati delle chiamate gi\u00e0 in volo non verranno salvati.</div>`;
    document.getElementById('submit-btn').disabled = false;
    loadSessions();
}

function updateProgressCard(data) {
    const sourcesContainer = document.getElementById('progress-sources');
    if (!sourcesContainer) return;

    // Mark completed sources
    const completedSources = new Set();
    for (const source of (data.sources || [])) {
        completedSources.add(source.source);

        const el = sourcesContainer.querySelector(`[data-source="${CSS.escape(source.source)}"]`);
        if (el) {
            const icon = el.querySelector('.progress-status-icon');
            const detail = el.querySelector('.progress-source-detail');

            const resultCount = source.result_count || source.items?.length || 0;
            const status = source.status || 'ok';

            if (status === 'error') {
                icon.textContent = '\u274C';
                icon.className = 'progress-status-icon error';
                detail.textContent = source.error || 'errore';
                detail.className = 'progress-source-detail error';
            } else {
                icon.textContent = '\u2705';
                icon.className = 'progress-status-icon done';

                const commentCount = source.items?.reduce((sum, item) =>
                    sum + (item.ai_comment_count || 0), 0) || 0;

                let detailText = `${resultCount} risultat${resultCount === 1 ? 'o' : 'i'}`;
                if (commentCount > 0) detailText += ` \u00B7 ${commentCount} commenti`;
                detail.textContent = detailText;
                detail.className = 'progress-source-detail done';
            }
        }
    }

    // Mark remaining sources as running (they're all parallel, so any not-completed is running)
    const allSourceEls = sourcesContainer.querySelectorAll('.progress-source');
    for (const el of allSourceEls) {
        const name = el.dataset.source;
        if (!completedSources.has(name)) {
            const icon = el.querySelector('.progress-status-icon');
            const detail = el.querySelector('.progress-source-detail');
            if (icon.className.includes('pending')) {
                icon.textContent = '\uD83D\uDD04';
                icon.className = 'progress-status-icon running';
                detail.textContent = 'scraping...';
                detail.className = 'progress-source-detail running';
            }
        }
    }
}

function formatElapsed(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
}


// ---------------------------------------------------------------------------
// Sessions
// ---------------------------------------------------------------------------

const SESSIONS_PER_PAGE = 10;
let _sessionsCache = [];
let _sessionsPage = 0;

async function loadSessions() {
    try {
        const resp = await fetch('/api/scraping-test/sessions', { credentials: 'same-origin' });
        if (!resp.ok) return;
        _sessionsCache = await resp.json();
        _sessionsPage = 0;
        renderSessionsPage();
    } catch (err) {
        console.error('Failed to load sessions:', err);
    }
}

function renderSessionsPage() {
    const panel = document.getElementById('sessions-panel');
    const list = document.getElementById('sessions-list');
    const countEl = document.getElementById('sessions-count');
    const pagEl = document.getElementById('sessions-pagination');

    const sessions = _sessionsCache || [];

    if (sessions.length === 0) {
        panel.style.display = 'none';
        return;
    }

    const totalPages = Math.max(1, Math.ceil(sessions.length / SESSIONS_PER_PAGE));
    if (_sessionsPage >= totalPages) _sessionsPage = totalPages - 1;
    if (_sessionsPage < 0) _sessionsPage = 0;

    panel.style.display = 'block';
    if (countEl) countEl.textContent = `${sessions.length}`;

    const start = _sessionsPage * SESSIONS_PER_PAGE;
    const end = Math.min(start + SESSIONS_PER_PAGE, sessions.length);
    const pageSlice = sessions.slice(start, end);

    list.innerHTML = '';
    for (const s of pageSlice) {
        const date = new Date(s.started_at);
        const dateStr = date.toLocaleDateString('it-IT', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });

        const statusIcon = s.status === 'completed' ? '\u2705' :
                           s.status === 'running' ? '\uD83D\uDD04' :
                           s.status === 'failed' ? '\u274C' :
                           s.status === 'cancelled' ? '\uD83D\uDEAB' : '\u26AA';

        const el = document.createElement('div');
        el.className = 'session-item';
        const phase = s.phase_filter || 'all';
        const phaseBadge = PHASE_BADGES[phase] || PHASE_BADGES.all;
        const motoreFilter = formatMotoreFilter(s.filter_alimentazione, s.filter_cilindrata);
        const motoreBadge = motoreFilter
            ? `<span class="motore-badge">${escapeHtml(motoreFilter)}</span>`
            : '';

        const flagClass = s.is_featured ? 'session-flag flagged' : 'session-flag';
        const flagTitle = s.is_featured ? 'Rimuovi da Anteprime' : 'Mostra in Anteprime';
        const flagIcon = s.is_featured ? '\u2605' : '\u2606';  // filled vs outline star

        el.innerHTML = `
            <div class="session-info" onclick="loadSession('${s.id}')">
                <strong>${statusIcon} ${escapeHtml(s.brand)}${s.model ? ' ' + escapeHtml(s.model) : ''}</strong>
                <span class="phase-badge ${phaseBadge.class}">${phaseBadge.label}</span>
                ${motoreBadge}
                <span class="session-date">${dateStr}</span>
                <span class="session-stats">${s.total_results} risultati \u00B7 ${s.total_comments} commenti</span>
            </div>
            <button class="${flagClass}" onclick="toggleSessionFlag('${s.id}', event)" title="${flagTitle}">${flagIcon}</button>
            <button class="session-delete" onclick="deleteSession('${s.id}', event)" title="Elimina">\u2715</button>
        `;
        list.appendChild(el);
    }

    // Pagination controls
    if (pagEl) {
        if (totalPages <= 1) {
            pagEl.innerHTML = '';
        } else {
            const prevDisabled = _sessionsPage === 0 ? 'disabled' : '';
            const nextDisabled = _sessionsPage >= totalPages - 1 ? 'disabled' : '';
            pagEl.innerHTML = `
                <button class="pag-btn" ${prevDisabled} onclick="gotoSessionsPage(${_sessionsPage - 1})">\u2039 Precedenti</button>
                <span class="pag-info">Pagina ${_sessionsPage + 1} di ${totalPages} \u00B7 mostra ${start + 1}\u2013${end} di ${sessions.length}</span>
                <button class="pag-btn" ${nextDisabled} onclick="gotoSessionsPage(${_sessionsPage + 1})">Successive \u203A</button>
            `;
        }
    }
}

function gotoSessionsPage(page) {
    _sessionsPage = page;
    renderSessionsPage();
}

async function loadSession(sessionId) {
    const loading = document.getElementById('loading');
    const resultsContainer = document.getElementById('results');
    const resultsMeta = document.getElementById('results-meta');

    loading.style.display = 'flex';
    resultsContainer.innerHTML = '';

    try {
        const resp = await fetch(`/api/scraping-test/sessions/${sessionId}`, { credentials: 'same-origin' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        renderResults(data, true);
    } catch (err) {
        resultsContainer.innerHTML = `<div class="error-banner">Errore: ${err.message}</div>`;
    } finally {
        loading.style.display = 'none';
    }
}

async function deleteSession(sessionId, event) {
    event.stopPropagation();
    if (!confirm('Eliminare questa sessione?')) return;

    try {
        await fetch(`/api/scraping-test/sessions/${sessionId}`, {
            method: 'DELETE',
            credentials: 'same-origin',
        });
        loadSessions();
    } catch (err) {
        console.error('Delete failed:', err);
    }
}

async function toggleSessionFlag(sessionId, event) {
    event.stopPropagation();
    try {
        const resp = await fetch(`/api/scraping-test/sessions/${sessionId}/flag`, {
            method: 'PATCH',
            credentials: 'same-origin',
        });
        if (!resp.ok) {
            console.error('Flag toggle failed:', resp.status);
            return;
        }
        // Update local cache + re-render current page without a full refetch
        const data = await resp.json();
        const s = _sessionsCache.find(x => x.id === sessionId);
        if (s) s.is_featured = data.is_featured;
        renderSessionsPage();
    } catch (err) {
        console.error('Flag toggle failed:', err);
    }
}


// ---------------------------------------------------------------------------
// Results Rendering — grouped by level (L1/L2/L3)
// ---------------------------------------------------------------------------

const LEVELS = [
    {
        key: 'L1',
        label: 'L1 — Comunicazione Ufficiale',
        icon: '\uD83C\uDFE2',
        description: 'Informazioni dai canali ufficiali del brand',
        types: ['official'],
    },
    {
        key: 'L2',
        label: 'L2 — Media e Giornalisti',
        icon: '\uD83D\uDCF0',
        description: 'Articoli, test e recensioni da fonti specializzate',
        types: ['news', 'perplexity'],
    },
    {
        key: 'L3',
        label: 'L3 — Commenti Utenti',
        icon: '\uD83D\uDCAC',
        description: 'Sentiment e opinioni da forum, social e YouTube',
        types: ['forum', 'youtube', 'social'],
    },
];

function getLevel(sourceType) {
    for (const level of LEVELS) {
        if (level.types.includes(sourceType)) return level.key;
    }
    return 'L3'; // default fallback
}

function renderResults(data, fromSession = false) {
    const resultsContainer = document.getElementById('results');
    const resultsMeta = document.getElementById('results-meta');

    // Meta info
    document.getElementById('meta-credits').textContent = `Credits Firecrawl: ${data.total_credits || 0}`;
    document.getElementById('meta-duration').textContent = `Durata: ${((data.total_duration_ms || 0) / 1000).toFixed(1)}s`;
    resultsMeta.style.display = 'flex';

    // Session badge
    const sessionBadge = document.getElementById('meta-session');
    if (fromSession && data.started_at) {
        const date = new Date(data.started_at);
        sessionBadge.textContent = `Sessione del ${date.toLocaleDateString('it-IT')}`;
        sessionBadge.style.display = 'inline';
    } else if (data.session_id) {
        sessionBadge.textContent = 'Salvata';
        sessionBadge.style.display = 'inline';
    } else {
        sessionBadge.style.display = 'none';
    }

    // Group sources by level
    const grouped = {};
    for (const level of LEVELS) {
        grouped[level.key] = [];
    }
    for (const source of (data.sources || [])) {
        const levelKey = getLevel(source.source_type);
        grouped[levelKey].push(source);
    }

    // Render level sections — skip levels not requested when a phase filter is active
    const brandName = data.brand || '';
    const phaseFilter = data.phase_filter || 'all';
    resultsContainer.innerHTML = '';

    // Motore filter banner (if filter was requested)
    const hasMotoreFilter = data.filter_alimentazione || data.filter_cilindrata != null;
    if (hasMotoreFilter) {
        const banner = buildMotoreFilterBanner(data);
        if (banner) resultsContainer.appendChild(banner);
    }

    for (const level of LEVELS) {
        if (phaseFilter !== 'all' && phaseFilter !== level.key) continue;
        const sources = grouped[level.key];
        if (sources.length === 0) continue;

        const totalResults = sources.reduce((sum, s) => sum + (s.result_count || s.items?.length || 0), 0);
        const totalComments = sources.reduce((sum, s) =>
            sum + (s.items || []).reduce((cs, item) => cs + (item.ai_comment_count || 0), 0), 0);

        const section = document.createElement('div');
        section.className = 'level-section';
        section.dataset.level = level.key;

        // Level header (clickable to expand/collapse)
        const header = document.createElement('div');
        header.className = 'level-header';
        header.innerHTML = `
            <div class="level-title">
                <span class="level-icon">${level.icon}</span>
                <h2>${level.label}</h2>
                <span class="level-count">${sources.length} font${sources.length === 1 ? 'e' : 'i'} &middot; ${totalResults} risultat${totalResults === 1 ? 'o' : 'i'}${totalComments > 0 ? ` &middot; ${totalComments} commenti` : ''}</span>
            </div>
            <span class="level-toggle">\u25BC</span>
        `;
        header.addEventListener('click', () => {
            section.classList.toggle('collapsed');
        });
        section.appendChild(header);

        // Level description
        const desc = document.createElement('div');
        desc.className = 'level-description';
        desc.textContent = level.description;
        section.appendChild(desc);

        // Source cards inside the level
        const body = document.createElement('div');
        body.className = 'level-body';
        for (const source of sources) {
            const card = createSourceCard(source, brandName);
            body.appendChild(card);
        }
        section.appendChild(body);

        resultsContainer.appendChild(section);
    }
}

function createSourceCard(source, brandName = '') {
    const icon = TYPE_ICONS[source.source_type] || '\uD83D\uDCC4';
    const info = { name: source.source, icon: icon };
    const status = STATUS_LABELS[source.status] || STATUS_LABELS.error;

    const card = document.createElement('div');
    card.className = 'source-card';

    const header = document.createElement('div');
    header.className = 'source-header';
    header.innerHTML = `
        <div class="source-title">
            <span class="source-icon">${info.icon}</span>
            <h3>${info.name}</h3>
            <span class="status-badge ${status.class}">${status.label}</span>
        </div>
        <div class="source-meta">
            <span>${source.result_count} risultati</span>
            ${source.credits_used ? `<span>${source.credits_used} credits</span>` : ''}
            <span>${((source.duration_ms || 0) / 1000).toFixed(1)}s</span>
        </div>
    `;
    card.appendChild(header);

    if (source.error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'source-error';
        errorDiv.textContent = source.error;
        card.appendChild(errorDiv);
    }

    if (source.items && source.items.length > 0) {
        // For L1 (official) sources, promote the driver-analysis card to the top,
        // always visible, and collapse the rest of the source items into a "Fonti"
        // dropdown. For L2/L3 keep the flat list.
        const isOfficial = source.source_type === 'official';
        let primaryItem = null;
        let restItems = source.items;

        if (isOfficial) {
            const idx = source.items.findIndex(
                it => it.ai_official_info && it.ai_official_info.is_driver_analysis
            );
            if (idx >= 0) {
                primaryItem = source.items[idx];
                restItems = source.items.filter((_, i) => i !== idx);
            }
        }

        if (primaryItem) {
            const primary = document.createElement('div');
            primary.className = 'source-primary';
            primary.innerHTML = `
                <div class="source-primary-header">
                    <span class="source-primary-badge">Scheda principale</span>
                    <span class="source-primary-sub">${escapeHtml(primaryItem.url || '')}</span>
                </div>
                ${renderOfficialInfo(primaryItem.ai_official_info)}
            `;
            card.appendChild(primary);
        }

        if (restItems.length > 0) {
            if (primaryItem) {
                // Collapsible "Fonti" container with individual item cards inside
                const fonti = document.createElement('details');
                fonti.className = 'source-fonti';
                const summary = document.createElement('summary');
                summary.innerHTML = `<span class="fonti-label">Fonti analizzate</span> <span class="fonti-count">${restItems.length}</span>`;
                fonti.appendChild(summary);

                const itemsList = document.createElement('div');
                itemsList.className = 'source-items';
                for (const item of restItems) {
                    const itemEl = createResultItem(item, source.source);
                    if (item.matches_filter === false) {
                        itemEl.classList.add('non-match');
                    }
                    itemsList.appendChild(itemEl);
                }
                fonti.appendChild(itemsList);
                card.appendChild(fonti);
            } else {
                // No primary card (L2/L3 or L1 without driver analysis): flat list
                const itemsList = document.createElement('div');
                itemsList.className = 'source-items';
                for (const item of restItems) {
                    const itemEl = createResultItem(item, source.source);
                    if (item.matches_filter === false) {
                        itemEl.classList.add('non-match');
                    }
                    itemsList.appendChild(itemEl);
                }
                card.appendChild(itemsList);
            }
        }
    }

    return card;
}

function createResultItem(item, sourceType) {
    const el = document.createElement('div');
    el.className = 'result-item';

    let title = item.title || item.url || 'Untitled';
    let subtitle = item.url || '';
    let badges = '';
    let contentHtml = '';

    if (item.scraped) {
        badges += `<span class="scrape-badge full">Contenuto completo</span>`;
    } else {
        badges += `<span class="scrape-badge snippet">Solo snippet</span>`;
    }

    if (item.content_length) {
        badges += `<span class="length-badge">${formatNumber(item.content_length)} chars</span>`;
    }

    if (item.ai_comments && item.ai_comments.length > 0) {
        badges += `<span class="scrape-badge ai">${item.ai_comment_count} commenti AI</span>`;
    }

    // Summary display
    let summaryHtml = '';
    if (item.summary) {
        summaryHtml = `<div class="item-summary">${escapeHtml(item.summary)}</div>`;
    }

    // Build content display
    // L1 citation item (lightweight, no AI extraction) — compact link + snippet
    if (item.perplexity_citation) {
        badges += `<span class="scrape-badge citation">Fonte citata</span>`;
        const host = (() => { try { return new URL(item.url).host.replace(/^www\./, ''); } catch { return item.url; } })();
        contentHtml = `
            <div class="citation-compact">
                <div class="citation-host">${escapeHtml(host)}</div>
                ${item.content ? `<div class="citation-text">${escapeHtml(item.content)}</div>` : ''}
                <a class="citation-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener">Apri fonte &rarr;</a>
            </div>`;
    }
    // 0. L1: Official brand communication (priority)
    else if (item.ai_official_info) {
        badges += `<span class="scrape-badge official">L1 Comunicazione ufficiale</span>`;
        contentHtml = renderOfficialInfo(item.ai_official_info);
        // For consolidated (Perplexity) items, append the full synthesis text expander
        if (item.ai_official_info.fonte_consolidata && item.content) {
            contentHtml += `<details class="official-fulltext">
                <summary>Testo sintesi completo</summary>
                <pre>${escapeHtml(item.content)}</pre>
            </details>`;
        }
    }
    // 1. AI-extracted comments (priority display)
    else if (item.ai_comments && item.ai_comments.length > 0) {
        contentHtml = renderAiComments(item.ai_comments);
    }
    // 2. Reddit/YouTube comments
    else if (item.comments && item.comments.length > 0) {
        if (item.channel) {
            subtitle = `${item.channel} \u00B7 ${formatNumber(item.view_count)} views \u00B7 ${formatNumber(item.like_count)} likes`;
        }
        const commentsText = item.comments.map(c => `\uD83D\uDCAC ${c}`).join('\n\n');
        contentHtml = `<pre>${escapeHtml((item.content || '') + '\n\n\u2501\u2501\u2501 Commenti (' + item.comments.length + ') \u2501\u2501\u2501\n\n' + commentsText)}</pre>`;
    }
    // 3. Raw content fallback
    else {
        contentHtml = `<pre>${escapeHtml(item.content || '')}</pre>`;
    }

    el.innerHTML = `
        <div class="item-header" onclick="this.parentElement.classList.toggle('expanded')">
            <strong>${escapeHtml(title)}</strong>
            <div class="item-badges">${badges}<span class="expand-icon">\u25BC</span></div>
        </div>
        <div class="item-subtitle">${escapeHtml(subtitle)}</div>
        ${summaryHtml}
        <div class="item-content">${contentHtml}</div>
    `;

    return el;
}

function renderAggregateOfficial(info) {
    const fmtEUR = (v) => v == null ? null : formatCurrency(v);
    let html = '<div class="official-info aggregate">';

    // Top banner — marketing positioning
    html += `<div class="agg-top">
        <span class="agg-badge">Scheda consolidata ufficiale</span>
        ${info.tono_comunicazione ? `<span class="agg-tono">${escapeHtml(info.tono_comunicazione)}</span>` : ''}
    </div>`;

    if (info.posizionamento_marketing) {
        html += `<div class="agg-positioning">${escapeHtml(info.posizionamento_marketing)}</div>`;
    }
    if (info.claim_principale) {
        html += `<div class="official-claim">&laquo;${escapeHtml(info.claim_principale)}&raquo;</div>`;
    }

    // Fascia prezzo + target (summary row)
    const fp = info.prezzi_finanziamenti?.fascia_prezzo || {};
    const summaryRow = [];
    if (fp.min_eur != null || fp.max_eur != null) {
        let priceText;
        if (fp.min_eur != null && fp.max_eur != null) priceText = `${fmtEUR(fp.min_eur)} – ${fmtEUR(fp.max_eur)}`;
        else if (fp.min_eur != null) priceText = `Da ${fmtEUR(fp.min_eur)}`;
        else priceText = `Fino a ${fmtEUR(fp.max_eur)}`;
        if (fp.note) priceText += ` (${escapeHtml(fp.note)})`;
        summaryRow.push(`<span class="agg-chip chip-price">${priceText}</span>`);
    }
    if (info.target_comunicato) {
        summaryRow.push(`<span class="agg-chip">Target: ${escapeHtml(info.target_comunicato)}</span>`);
    }
    if (summaryRow.length) html += `<div class="agg-chips">${summaryRow.join('')}</div>`;

    // Allestimenti
    const allestimenti = info.allestimenti || [];
    if (allestimenti.length) {
        html += `<div class="agg-section"><h4>Allestimenti (${allestimenti.length})</h4><table class="official-tech-table"><thead><tr>
            <th>Nome</th><th>Posizionamento</th><th>Prezzo</th><th>Disponibile su</th><th>Note</th>
        </tr></thead><tbody>`;
        for (const a of allestimenti) {
            html += `<tr>
                <td><strong>${escapeHtml(a.nome || '—')}</strong></td>
                <td>${escapeHtml(a.posizionamento || '—')}</td>
                <td>${a.prezzo_eur != null ? fmtEUR(a.prezzo_eur) : '—'}</td>
                <td>${(a.disponibile_su || []).map(s => `<span class="topic-tag">${escapeHtml(s)}</span>`).join(' ') || '—'}</td>
                <td class="cell-note">${escapeHtml(a.prezzo_note || '')}</td>
            </tr>`;
        }
        html += `</tbody></table></div>`;
    }

    // Motorizzazioni
    const motori = info.motorizzazioni || [];
    if (motori.length) {
        html += `<div class="agg-section"><h4>Motorizzazioni (${motori.length})</h4><table class="official-tech-table"><thead><tr>
            <th>Nome</th><th>Alim.</th><th>cc</th><th>L</th><th>CV</th><th>kW</th><th>Nm</th><th>Cil.</th><th>Cambio</th><th>Trazione</th>
        </tr></thead><tbody>`;
        for (const m of motori) {
            const t = m.trasmissione || {};
            const cambio = [t.tipo, t.marce ? `${t.marce} marce` : null].filter(Boolean).join(' · ');
            html += `<tr>
                <td><strong>${escapeHtml(m.nome_commerciale || '—')}</strong></td>
                <td>${escapeHtml(ALIMENTAZIONE_LABEL[m.alimentazione] || m.alimentazione || '—')}</td>
                <td>${m.cilindrata_cc ?? '—'}</td>
                <td>${m.cilindrata_l ?? '—'}</td>
                <td>${m.cv ?? '—'}</td>
                <td>${m.kw ?? '—'}</td>
                <td>${m.coppia_nm ?? '—'}</td>
                <td>${m.cilindri ?? '—'}</td>
                <td>${escapeHtml(cambio || '—')}</td>
                <td>${escapeHtml(t.trazione || '—')}</td>
            </tr>`;
        }
        html += `</tbody></table></div>`;
    }

    // Consumi ed emissioni
    const consumi = info.consumi_emissioni || [];
    if (consumi.length) {
        html += `<div class="agg-section"><h4>Consumi ed emissioni</h4><table class="official-tech-table"><thead><tr>
            <th>Motorizzazione</th><th>WLTP L/100km</th><th>WLTP kWh/100km</th><th>CO2 g/km</th><th>Classe</th><th>Autonomia EV km</th><th>Autonomia tot. km</th>
        </tr></thead><tbody>`;
        for (const c of consumi) {
            html += `<tr>
                <td>${escapeHtml(c.motorizzazione || '—')}</td>
                <td>${c.wltp_combinato_l_100km ?? '—'}</td>
                <td>${c.wltp_combinato_kwh_100km ?? '—'}</td>
                <td>${c.emissioni_co2_gkm ?? '—'}</td>
                <td>${escapeHtml(c.classe_emissioni || '—')}</td>
                <td>${c.autonomia_elettrica_km ?? '—'}</td>
                <td>${c.autonomia_totale_km ?? '—'}</td>
            </tr>`;
        }
        html += `</tbody></table></div>`;
    }

    // Promozioni finanziarie
    const promo = info.prezzi_finanziamenti?.promozioni || [];
    if (promo.length) {
        html += `<div class="agg-section"><h4>Finanziamenti e promozioni (${promo.length})</h4><table class="official-tech-table"><thead><tr>
            <th>Tipo</th><th>Descrizione</th><th>Anticipo</th><th>Rata</th><th>Durata</th><th>TAN</th><th>TAEG</th><th>Scadenza</th>
        </tr></thead><tbody>`;
        for (const p of promo) {
            html += `<tr>
                <td>${escapeHtml(p.tipo || '—')}</td>
                <td>${escapeHtml(p.descrizione || '—')}</td>
                <td>${p.anticipo_eur != null ? fmtEUR(p.anticipo_eur) : '—'}</td>
                <td>${p.rata_mensile_eur != null ? fmtEUR(p.rata_mensile_eur) + '/m' : '—'}</td>
                <td>${p.durata_mesi != null ? p.durata_mesi + ' mesi' : '—'}</td>
                <td>${p.tan_percent != null ? p.tan_percent + '%' : '—'}</td>
                <td>${p.taeg_percent != null ? p.taeg_percent + '%' : '—'}</td>
                <td>${escapeHtml(p.scadenza || '—')}</td>
            </tr>`;
        }
        html += `</tbody></table></div>`;
    }

    // Dimensioni
    const d = info.dimensioni || {};
    const hasD = Object.values(d).some(v => v != null && v !== '');
    if (hasD) {
        const cell = (label, val, unit) => val != null
            ? `<div class="dim-cell"><span class="dim-label">${label}</span><span class="dim-value">${val} ${unit}</span></div>`
            : '';
        html += `<div class="agg-section"><h4>Dimensioni e pesi</h4><div class="official-dims">
            ${cell('Lunghezza', d.lunghezza_mm, 'mm')}
            ${cell('Larghezza', d.larghezza_mm, 'mm')}
            ${cell('Altezza', d.altezza_mm, 'mm')}
            ${cell('Passo', d.passo_mm, 'mm')}
            ${cell('Peso', d.peso_kg, 'kg')}
            ${cell('Serbatoio', d.serbatoio_l, 'L')}
            ${cell('Bagagliaio min', d.bagagliaio_min_l, 'L')}
            ${cell('Bagagliaio max', d.bagagliaio_max_l, 'L')}
        </div></div>`;
    }

    // Sicurezza ADAS
    const adas = info.sicurezza_adas || {};
    const adasSerie = adas.di_serie || [];
    const adasOpt = adas.opzionali || [];
    if (adasSerie.length || adasOpt.length || adas.note) {
        html += `<div class="agg-section"><h4>Sicurezza &amp; ADAS</h4>`;
        if (adasSerie.length) {
            html += `<div class="adas-row"><strong>Di serie:</strong> ${adasSerie.map(x => `<span class="topic-tag adas-serie">${escapeHtml(x)}</span>`).join(' ')}</div>`;
        }
        if (adasOpt.length) {
            html += `<div class="adas-row"><strong>Opzionali:</strong> ${adasOpt.map(x => `<span class="topic-tag adas-opt">${escapeHtml(x)}</span>`).join(' ')}</div>`;
        }
        if (adas.note) html += `<div class="adas-note">${escapeHtml(adas.note)}</div>`;
        html += `</div>`;
    }

    // Colori disponibili
    const colori = info.colori_disponibili || [];
    if (colori.length) {
        html += `<div class="agg-section"><h4>Colori disponibili (${colori.length})</h4><div class="colors-grid">`;
        for (const c of colori) {
            const priceTag = c.prezzo_eur === 0 ? '<span class="color-price free">incluso</span>'
                : (c.prezzo_eur != null ? `<span class="color-price">${fmtEUR(c.prezzo_eur)}</span>` : '');
            html += `<div class="color-cell">
                <div class="color-name">${escapeHtml(c.nome || '—')}</div>
                <div class="color-type">${escapeHtml(c.tipo || '')}</div>
                ${priceTag}
            </div>`;
        }
        html += `</div></div>`;
    }

    // Dotazione per allestimento
    const dotMap = info.dotazione_per_allestimento || {};
    const dotNames = Object.keys(dotMap);
    if (dotNames.length) {
        html += `<div class="agg-section"><h4>Dotazione di serie per allestimento</h4>`;
        for (const name of dotNames) {
            const list = dotMap[name] || [];
            if (!list.length) continue;
            html += `<details class="dotazione-trim"><summary><strong>${escapeHtml(name)}</strong> (${list.length})</summary><div class="dotazione-list">`;
            for (const d of list) html += `<span class="dotazione-item">${escapeHtml(d)}</span>`;
            html += `</div></details>`;
        }
        html += `</div>`;
    }

    // Optionals
    const opts = info.optionals_disponibili || [];
    if (opts.length) {
        html += `<div class="agg-section"><h4>Optionals disponibili (${opts.length})</h4><table class="official-tech-table"><thead><tr>
            <th>Nome</th><th>Categoria</th><th>Prezzo</th><th>Disponibile su</th><th>Descrizione</th>
        </tr></thead><tbody>`;
        for (const o of opts) {
            html += `<tr>
                <td><strong>${escapeHtml(o.nome || '—')}</strong></td>
                <td>${escapeHtml(o.categoria || '—')}</td>
                <td>${o.prezzo_eur != null ? fmtEUR(o.prezzo_eur) : '—'}</td>
                <td>${(o.disponibile_su || []).map(s => `<span class="topic-tag">${escapeHtml(s)}</span>`).join(' ') || '—'}</td>
                <td class="cell-note">${escapeHtml(o.descrizione || '')}</td>
            </tr>`;
        }
        html += `</tbody></table></div>`;
    }

    // Materiali costruttivi
    const mat = info.materiali_costruttivi || {};
    const hasMat = ['carrozzeria', 'interni', 'sostenibilita'].some(k => (mat[k] || []).length);
    if (hasMat) {
        html += `<div class="agg-section"><h4>Materiali costruttivi</h4>`;
        if ((mat.carrozzeria || []).length) html += `<div class="mat-row"><strong>Carrozzeria:</strong> ${mat.carrozzeria.map(x => `<span class="topic-tag">${escapeHtml(x)}</span>`).join(' ')}</div>`;
        if ((mat.interni || []).length) html += `<div class="mat-row"><strong>Interni:</strong> ${mat.interni.map(x => `<span class="topic-tag">${escapeHtml(x)}</span>`).join(' ')}</div>`;
        if ((mat.sostenibilita || []).length) html += `<div class="mat-row"><strong>Sostenibilità:</strong> ${mat.sostenibilita.map(x => `<span class="topic-tag">${escapeHtml(x)}</span>`).join(' ')}</div>`;
        html += `</div>`;
    }

    // Peculiarità
    const pec = info.peculiarita || [];
    if (pec.length) {
        html += `<div class="agg-section"><h4>Peculiarità</h4><ul class="pec-list">`;
        for (const p of pec) html += `<li>${escapeHtml(p)}</li>`;
        html += `</ul></div>`;
    }

    // Note divergenze tra fonti
    if (info.note_discrepanze) {
        html += `<div class="agg-section disc"><h4>Note / divergenze tra fonti</h4><div class="disc-note">${escapeHtml(info.note_discrepanze)}</div></div>`;
    }

    // Fonti citate
    const fonti = info.fonti_citate || [];
    if (fonti.length > 0) {
        html += `<details class="official-citations">
            <summary>Fonti citate (${fonti.length})</summary>
            <ul>`;
        for (const f of fonti) {
            const label = f.title || f.url;
            html += `<li><a href="${escapeHtml(f.url)}" target="_blank" rel="noopener">${escapeHtml(label)}</a>`;
            if (f.snippet) html += `<div class="citation-snippet">${escapeHtml(f.snippet)}</div>`;
            html += `</li>`;
        }
        html += `</ul></details>`;
    }

    html += '</div>';
    return html;
}

function renderAiComments(comments) {
    const SENTIMENT_ICONS = { positivo: '\uD83D\uDFE2', negativo: '\uD83D\uDD34', neutro: '\u26AA', misto: '\uD83D\uDFE1' };

    let html = '<div class="ai-comments">';
    for (const c of comments) {
        const icon = SENTIMENT_ICONS[c.sentiment] || '\u26AA';
        const topics = (c.topics || []).map(t => `<span class="topic-tag">${escapeHtml(t)}</span>`).join(' ');
        const mm = c.motore_menzionato;
        const motoreTag = mm
            ? `<span class="motore-tag-inline">${escapeHtml(formatMotoreFilter(mm.alimentazione, mm.cilindrata) || '')}</span>`
            : '';
        const nonMatchCls = c.matches_filter === false ? ' non-match' : '';
        html += `
            <div class="ai-comment${nonMatchCls}">
                <div class="ai-comment-header">
                    <span class="sentiment-icon">${icon}</span>
                    <strong>${escapeHtml(c.author || 'anonimo')}</strong>
                    <span class="sentiment-label ${c.sentiment}">${c.sentiment}</span>
                    ${topics}
                    ${motoreTag}
                </div>
                <div class="ai-comment-text">${escapeHtml(c.text)}</div>
            </div>`;
    }
    html += '</div>';
    return html;
}

const DRIVER_LABELS = {
    design_linea: 'Design & Linea',
    prezzo_accessibilita: 'Prezzo & Accessibilità',
    tecnologia_innovazione: 'Tecnologia & Innovazione',
    sicurezza_adas: 'Sicurezza & ADAS',
    consumi_sostenibilita: 'Consumi & Sostenibilità',
    prestazioni_guida: 'Prestazioni & Piacere di guida',
    spazio_praticita: 'Spazio & Praticità',
    heritage_identita: 'Heritage & Identità brand',
    lifestyle_emozione: 'Lifestyle & Emozione',
};

const CANALE_LABELS = {
    sito_brand: 'sito brand',
    youtube: 'YouTube',
    perplexity: 'Perplexity',
};

function renderDriverAnalysis(info) {
    let html = '<div class="official-info driver-analysis">';

    html += `<div class="agg-top">
        <span class="agg-badge">L1 Driver comunicativi ufficiali</span>
        ${info.target_comunicato ? `<span class="agg-tono">Target: ${escapeHtml(info.target_comunicato)}</span>` : ''}
    </div>`;

    if (info.tagline_campagna) {
        html += `<div class="official-claim">&laquo;${escapeHtml(info.tagline_campagna)}&raquo;</div>`;
    }

    const ranking = Array.isArray(info.ranking_driver) ? info.ranking_driver : [];
    const active = ranking.filter(d => (d.peso || 0) > 0);
    const maxPeso = active.reduce((m, d) => Math.max(m, d.peso || 0), 0) || 1;

    if (active.length > 0) {
        html += `<div class="driver-chart">`;
        for (const d of active) {
            const label = DRIVER_LABELS[d.driver] || d.driver;
            const pct = Math.max(2, Math.round((d.peso / maxPeso) * 100));
            html += `
                <div class="driver-row">
                    <div class="driver-row-label"><strong>${escapeHtml(label)}</strong><span class="driver-row-peso">${d.peso}%</span></div>
                    <div class="driver-row-bar"><div class="driver-row-fill" style="width:${pct}%"></div></div>
                </div>`;
        }
        html += `</div>`;
    }

    // Per-driver detail cards
    if (active.length > 0) {
        html += `<div class="driver-details">`;
        for (const d of active) {
            const label = DRIVER_LABELS[d.driver] || d.driver;
            const claims = Array.isArray(d.claim_esemplificativi) ? d.claim_esemplificativi : [];
            const canali = Array.isArray(d.canali) ? d.canali : [];
            html += `<div class="driver-card">
                <div class="driver-card-header">
                    <strong>${escapeHtml(label)}</strong>
                    <span class="driver-card-peso">${d.peso}%</span>
                </div>`;
            if (d.evidenze) {
                html += `<div class="driver-card-evidence">${escapeHtml(d.evidenze)}</div>`;
            }
            if (claims.length > 0) {
                html += `<ul class="driver-card-claims">`;
                for (const c of claims) {
                    html += `<li>&laquo;${escapeHtml(c)}&raquo;</li>`;
                }
                html += `</ul>`;
            }
            if (canali.length > 0) {
                const labels = canali.map(x => CANALE_LABELS[x] || x).join(', ');
                html += `<div class="driver-card-canali">Canali: ${escapeHtml(labels)}</div>`;
            }
            html += `</div>`;
        }
        html += `</div>`;
    }

    // Drivers not used (peso=0) — compact
    const inactive = ranking.filter(d => !((d.peso || 0) > 0));
    if (inactive.length > 0) {
        const names = inactive.map(d => DRIVER_LABELS[d.driver] || d.driver).join(', ');
        html += `<div class="driver-inactive"><em>Driver non comunicati:</em> ${escapeHtml(names)}</div>`;
    }

    if (info.note_metodologiche) {
        html += `<details class="driver-notes">
            <summary>Note metodologiche</summary>
            <div>${escapeHtml(info.note_metodologiche)}</div>
        </details>`;
    }

    // Sources row (Perplexity citations)
    const fonti = Array.isArray(info.fonti_citate) ? info.fonti_citate : [];
    if (fonti.length > 0) {
        html += `<details class="driver-sources">
            <summary>Fonti citate (${fonti.length})</summary>
            <ul>`;
        for (const f of fonti) {
            const t = f.title || f.url;
            html += `<li><a href="${escapeHtml(f.url)}" target="_blank" rel="noopener">${escapeHtml(t)}</a></li>`;
        }
        html += `</ul></details>`;
    }

    html += '</div>';
    return html;
}

function renderOfficialInfo(info) {
    // Phase A pilot: communication drivers analysis replaces the tech-specs aggregate
    if (info.is_driver_analysis) {
        return renderDriverAnalysis(info);
    }
    // Legacy tech-specs aggregate (disabled by default — see L1_LEGACY_AGGREGATE flag)
    if (info.is_aggregate) {
        return renderAggregateOfficial(info);
    }

    let html = '<div class="official-info">';

    // Type + Positioning
    const tipoLabel = {
        pagina_prodotto: 'Pagina Prodotto', promozione: 'Promozione',
        comunicato_stampa: 'Comunicato Stampa', video: 'Video Ufficiale',
        configuratore: 'Configuratore', listino: 'Listino',
    };
    const tipo = tipoLabel[info.tipo_contenuto] || info.tipo_contenuto || 'Contenuto';
    html += `<div class="official-tipo"><span class="official-tipo-badge">${escapeHtml(tipo)}</span>`;
    if (info.fonte_consolidata) {
        html += ` <span class="official-consolidated">Ufficiale consolidato (Perplexity)</span>`;
    }
    if (info.tono_comunicazione) {
        html += ` <span class="official-tono">${escapeHtml(info.tono_comunicazione)}</span>`;
    }
    html += `</div>`;

    if (info.posizionamento) {
        html += `<div class="official-positioning"><strong>Posizionamento:</strong> ${escapeHtml(info.posizionamento)}</div>`;
    }
    if (info.claim_principale) {
        html += `<div class="official-claim">&laquo;${escapeHtml(info.claim_principale)}&raquo;</div>`;
    }

    if (info.punti_di_forza_comunicati && info.punti_di_forza_comunicati.length > 0) {
        html += `<div class="official-section"><strong>Punti di forza comunicati:</strong><ul>`;
        for (const p of info.punti_di_forza_comunicati) {
            html += `<li>${escapeHtml(p)}</li>`;
        }
        html += `</ul></div>`;
    }

    if (info.prezzo && (info.prezzo.da || info.prezzo.a)) {
        let priceText = '';
        if (info.prezzo.da && info.prezzo.a) {
            priceText = `Da ${formatCurrency(info.prezzo.da)} a ${formatCurrency(info.prezzo.a)}`;
        } else if (info.prezzo.da) {
            priceText = `Da ${formatCurrency(info.prezzo.da)}`;
        } else {
            priceText = `Fino a ${formatCurrency(info.prezzo.a)}`;
        }
        if (info.prezzo.note) priceText += ` (${escapeHtml(info.prezzo.note)})`;
        html += `<div class="official-price"><strong>Prezzo:</strong> ${priceText}</div>`;
    }

    if (info.promozioni_attive && info.promozioni_attive.length > 0) {
        html += `<div class="official-section"><strong>Promozioni attive:</strong><ul>`;
        for (const promo of info.promozioni_attive) {
            let promoText = escapeHtml(promo.descrizione || promo.tipo || '');
            if (promo.rata_mensile) promoText += ` \u2014 rata ${formatCurrency(promo.rata_mensile)}/mese`;
            html += `<li>${promoText}</li>`;
        }
        html += `</ul></div>`;
    }

    if (info.versioni_disponibili && info.versioni_disponibili.length > 0) {
        html += `<div class="official-tags"><strong>Versioni:</strong> `;
        html += info.versioni_disponibili.map(v => `<span class="topic-tag">${escapeHtml(v)}</span>`).join(' ');
        html += `</div>`;
    }
    if (info.motorizzazioni_citate && info.motorizzazioni_citate.length > 0) {
        html += `<div class="official-tags"><strong>Motorizzazioni:</strong> `;
        html += info.motorizzazioni_citate.map(m => `<span class="topic-tag engine">${escapeHtml(m)}</span>`).join(' ');
        html += `</div>`;
    }

    if (info.caratteristiche_evidenziate && info.caratteristiche_evidenziate.length > 0) {
        html += `<div class="official-tags"><strong>Caratteristiche evidenziate:</strong> `;
        html += info.caratteristiche_evidenziate.map(f => `<span class="topic-tag feature">${escapeHtml(f)}</span>`).join(' ');
        html += `</div>`;
    }
    if (info.target_comunicato) {
        html += `<div class="official-target"><strong>Target:</strong> ${escapeHtml(info.target_comunicato)}</div>`;
    }

    // Technical data: prestazioni per versione
    const prestazioni = info.prestazioni_per_versione || [];
    if (prestazioni.length > 0) {
        html += `<div class="official-tech-block"><strong>Prestazioni per versione:</strong><table class="official-tech-table"><thead><tr>
            <th>Versione</th><th>Alim.</th><th>cc</th><th>CV</th><th>kW</th><th>Nm</th><th>Cambio</th><th>Trazione</th><th>0-100</th><th>V.max</th>
            </tr></thead><tbody>`;
        for (const p of prestazioni) {
            html += `<tr>
                <td>${escapeHtml(p.versione || '—')}</td>
                <td>${escapeHtml(ALIMENTAZIONE_LABEL[p.alimentazione] || p.alimentazione || '—')}</td>
                <td>${p.cilindrata_cc ?? '—'}</td>
                <td>${p.cv ?? '—'}</td>
                <td>${p.kw ?? '—'}</td>
                <td>${p.coppia_nm ?? '—'}</td>
                <td>${escapeHtml(p.cambio || '—')}</td>
                <td>${escapeHtml(p.trazione || '—')}</td>
                <td>${p.zero_cento_s != null ? p.zero_cento_s + ' s' : '—'}</td>
                <td>${p.velocita_max_kmh != null ? p.velocita_max_kmh + ' km/h' : '—'}</td>
            </tr>`;
        }
        html += `</tbody></table></div>`;
    }

    // Consumi
    const consumi = info.consumi_per_versione || [];
    if (consumi.length > 0) {
        html += `<div class="official-tech-block"><strong>Consumi ed emissioni:</strong><table class="official-tech-table"><thead><tr>
            <th>Versione</th><th>WLTP (L/100km)</th><th>WLTP (kWh/100km)</th><th>CO2 (g/km)</th><th>Classe</th><th>Autonomia EV (km)</th>
            </tr></thead><tbody>`;
        for (const c of consumi) {
            html += `<tr>
                <td>${escapeHtml(c.versione || '—')}</td>
                <td>${c.wltp_combinato_l_100km ?? '—'}</td>
                <td>${c.wltp_combinato_kwh_100km ?? '—'}</td>
                <td>${c.emissioni_co2_gkm ?? '—'}</td>
                <td>${escapeHtml(c.classe_emissioni || '—')}</td>
                <td>${c.autonomia_elettrica_km ?? '—'}</td>
            </tr>`;
        }
        html += `</tbody></table></div>`;
    }

    // Dimensioni
    const dim = info.dimensioni || {};
    const hasDim = Object.values(dim).some(v => v != null && v !== '');
    if (hasDim) {
        const fmt = (label, val, unit) => val != null ? `<div class="dim-cell"><span class="dim-label">${label}</span><span class="dim-value">${val} ${unit}</span></div>` : '';
        html += `<div class="official-tech-block"><strong>Dimensioni e pesi:</strong><div class="official-dims">
            ${fmt('Lunghezza', dim.lunghezza_mm, 'mm')}
            ${fmt('Larghezza', dim.larghezza_mm, 'mm')}
            ${fmt('Altezza', dim.altezza_mm, 'mm')}
            ${fmt('Passo', dim.passo_mm, 'mm')}
            ${fmt('Peso', dim.peso_kg, 'kg')}
            ${fmt('Serbatoio', dim.serbatoio_l, 'L')}
            ${fmt('Bagagliaio min', dim.bagagliaio_min_l, 'L')}
            ${fmt('Bagagliaio max', dim.bagagliaio_max_l, 'L')}
        </div></div>`;
    }

    // Garanzia
    if (info.garanzia && (info.garanzia.anni || info.garanzia.km)) {
        const g = info.garanzia;
        let gText = '';
        if (g.anni) gText += `${g.anni} anni`;
        if (g.km) gText += (gText ? ' / ' : '') + `${g.km.toLocaleString('it-IT')} km`;
        if (g.note) gText += ` (${g.note})`;
        html += `<div class="official-warranty"><strong>Garanzia:</strong> ${escapeHtml(gText)}</div>`;
    }

    // Dotazione dettagliata
    const dotazione = info.dotazione_dettagliata || [];
    if (dotazione.length > 0) {
        html += `<details class="official-dotazione">
            <summary>Dotazione dettagliata (${dotazione.length})</summary>
            <div class="dotazione-list">`;
        for (const d of dotazione) {
            html += `<span class="dotazione-item">${escapeHtml(d)}</span>`;
        }
        html += `</div></details>`;
    }

    // Citations list (from Perplexity consolidated items)
    const fonti = info.fonti_citate || [];
    if (fonti.length > 0) {
        html += `<details class="official-citations">
            <summary>Fonti citate (${fonti.length})</summary>
            <ul>`;
        for (const f of fonti) {
            const label = f.title || f.url;
            html += `<li><a href="${escapeHtml(f.url)}" target="_blank" rel="noopener">${escapeHtml(label)}</a>`;
            if (f.snippet) {
                html += `<div class="citation-snippet">${escapeHtml(f.snippet)}</div>`;
            }
            html += `</li>`;
        }
        html += `</ul></details>`;
    }

    html += '</div>';
    return html;
}


// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function formatCurrency(amount) {
    if (!amount) return '\u2014';
    return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(amount);
}

function formatNumber(n) {
    if (!n) return '0';
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
