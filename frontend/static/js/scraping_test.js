// UNICAB — Scraping Test Frontend

const TYPE_ICONS = {
    forum: '\uD83D\uDCAC',
    news: '\uD83D\uDCF0',
    youtube: '\u25B6\uFE0F',
    social: '\uD83D\uDC65',
};

const STATUS_LABELS = {
    ok: { label: 'OK', class: 'status-ok' },
    partial: { label: 'Parziale', class: 'status-partial' },
    error: { label: 'Errore', class: 'status-error' },
};

// Load previous sessions on page load
document.addEventListener('DOMContentLoaded', loadSessions);

document.getElementById('scraping-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const brand = document.getElementById('brand').value.trim();
    const model = document.getElementById('model').value.trim();
    if (!brand) return;

    const submitBtn = document.getElementById('submit-btn');
    const loading = document.getElementById('loading');
    const resultsContainer = document.getElementById('results');
    const resultsMeta = document.getElementById('results-meta');

    // Reset
    submitBtn.disabled = true;
    loading.style.display = 'flex';
    resultsContainer.innerHTML = '';
    resultsMeta.style.display = 'none';

    try {
        // Cookie is sent automatically (httponly), no need for Authorization header
        const resp = await fetch('/api/scraping-test/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ brand, model }),
        });

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        renderResults(data);
        // Refresh sessions list
        loadSessions();

    } catch (err) {
        resultsContainer.innerHTML = `<div class="error-banner">Errore: ${err.message}</div>`;
    } finally {
        submitBtn.disabled = false;
        loading.style.display = 'none';
    }
});

async function loadSessions() {
    try {
        const resp = await fetch('/api/scraping-test/sessions', { credentials: 'same-origin' });
        if (!resp.ok) return;
        const sessions = await resp.json();

        const panel = document.getElementById('sessions-panel');
        const list = document.getElementById('sessions-list');

        if (!sessions || sessions.length === 0) {
            panel.style.display = 'none';
            return;
        }

        panel.style.display = 'block';
        list.innerHTML = '';

        for (const s of sessions) {
            const date = new Date(s.started_at);
            const dateStr = date.toLocaleDateString('it-IT', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit',
            });

            const el = document.createElement('div');
            el.className = 'session-item';
            el.innerHTML = `
                <div class="session-info" onclick="loadSession('${s.id}')">
                    <strong>${escapeHtml(s.brand)}${s.model ? ' ' + escapeHtml(s.model) : ''}</strong>
                    <span class="session-date">${dateStr}</span>
                    <span class="session-stats">${s.total_results} risultati \u00B7 ${s.total_comments} commenti</span>
                </div>
                <button class="session-delete" onclick="deleteSession('${s.id}', event)" title="Elimina">\u2715</button>
            `;
            list.appendChild(el);
        }
    } catch (err) {
        console.error('Failed to load sessions:', err);
    }
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

function renderResults(data, fromSession = false) {
    const resultsContainer = document.getElementById('results');
    const resultsMeta = document.getElementById('results-meta');

    // Meta info
    document.getElementById('meta-credits').textContent = `Credits Firecrawl: ${data.total_credits}`;
    document.getElementById('meta-duration').textContent = `Durata: ${(data.total_duration_ms / 1000).toFixed(1)}s`;
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

    // Source cards
    resultsContainer.innerHTML = '';
    for (const source of data.sources) {
        const card = createSourceCard(source);
        resultsContainer.appendChild(card);
    }
}

function createSourceCard(source) {
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
            <span>${(source.duration_ms / 1000).toFixed(1)}s</span>
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
        const itemsList = document.createElement('div');
        itemsList.className = 'source-items';

        for (const item of source.items) {
            const itemEl = createResultItem(item, source.source);
            itemsList.appendChild(itemEl);
        }

        card.appendChild(itemsList);
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
    // 1. AI-extracted comments (priority display)
    if (item.ai_comments && item.ai_comments.length > 0) {
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

function renderAiComments(comments) {
    const SENTIMENT_ICONS = { positivo: '\uD83D\uDFE2', negativo: '\uD83D\uDD34', neutro: '\u26AA', misto: '\uD83D\uDFE1' };

    let html = '<div class="ai-comments">';
    for (const c of comments) {
        const icon = SENTIMENT_ICONS[c.sentiment] || '\u26AA';
        const topics = (c.topics || []).map(t => `<span class="topic-tag">${escapeHtml(t)}</span>`).join(' ');
        html += `
            <div class="ai-comment">
                <div class="ai-comment-header">
                    <span class="sentiment-icon">${icon}</span>
                    <strong>${escapeHtml(c.author || 'anonimo')}</strong>
                    <span class="sentiment-label ${c.sentiment}">${c.sentiment}</span>
                    ${topics}
                </div>
                <div class="ai-comment-text">${escapeHtml(c.text)}</div>
            </div>`;
    }
    html += '</div>';
    return html;
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
