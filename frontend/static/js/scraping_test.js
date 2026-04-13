// UNICAB — Scraping Test Frontend

const TYPE_ICONS = {
    forum: '\uD83D\uDCAC',
    news: '\uD83D\uDCF0',
    youtube: '\u25B6\uFE0F',
    social: '\uD83D\uDC65',
    official: '\uD83C\uDFE2',
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
    // 0. L1: Official brand communication (priority)
    if (item.ai_official_info) {
        badges += `<span class="scrape-badge official">L1 Comunicazione ufficiale</span>`;
        contentHtml = renderOfficialInfo(item.ai_official_info);
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

function renderOfficialInfo(info) {
    let html = '<div class="official-info">';

    // Type + Positioning
    const tipoLabel = {
        pagina_prodotto: 'Pagina Prodotto', promozione: 'Promozione',
        comunicato_stampa: 'Comunicato Stampa', video: 'Video Ufficiale',
        configuratore: 'Configuratore', listino: 'Listino',
    };
    const tipo = tipoLabel[info.tipo_contenuto] || info.tipo_contenuto || 'Contenuto';
    html += `<div class="official-tipo"><span class="official-tipo-badge">${escapeHtml(tipo)}</span>`;
    if (info.tono_comunicazione) {
        html += ` <span class="official-tono">${escapeHtml(info.tono_comunicazione)}</span>`;
    }
    html += `</div>`;

    // Positioning & Claim
    if (info.posizionamento) {
        html += `<div class="official-positioning"><strong>Posizionamento:</strong> ${escapeHtml(info.posizionamento)}</div>`;
    }
    if (info.claim_principale) {
        html += `<div class="official-claim">&laquo;${escapeHtml(info.claim_principale)}&raquo;</div>`;
    }

    // Selling points
    if (info.punti_di_forza_comunicati && info.punti_di_forza_comunicati.length > 0) {
        html += `<div class="official-section"><strong>Punti di forza comunicati:</strong><ul>`;
        for (const p of info.punti_di_forza_comunicati) {
            html += `<li>${escapeHtml(p)}</li>`;
        }
        html += `</ul></div>`;
    }

    // Price
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

    // Promotions
    if (info.promozioni_attive && info.promozioni_attive.length > 0) {
        html += `<div class="official-section"><strong>Promozioni attive:</strong><ul>`;
        for (const promo of info.promozioni_attive) {
            let promoText = escapeHtml(promo.descrizione || promo.tipo || '');
            if (promo.rata_mensile) promoText += ` — rata ${formatCurrency(promo.rata_mensile)}/mese`;
            html += `<li>${promoText}</li>`;
        }
        html += `</ul></div>`;
    }

    // Versions & Engines
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

    // Features & Target
    if (info.caratteristiche_evidenziate && info.caratteristiche_evidenziate.length > 0) {
        html += `<div class="official-tags"><strong>Caratteristiche evidenziate:</strong> `;
        html += info.caratteristiche_evidenziate.map(f => `<span class="topic-tag feature">${escapeHtml(f)}</span>`).join(' ');
        html += `</div>`;
    }
    if (info.target_comunicato) {
        html += `<div class="official-target"><strong>Target:</strong> ${escapeHtml(info.target_comunicato)}</div>`;
    }

    html += '</div>';
    return html;
}

function formatCurrency(amount) {
    if (!amount) return '—';
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
