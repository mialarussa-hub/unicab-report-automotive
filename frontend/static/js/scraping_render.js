// UNICAB — Shared rendering module for scraping sessions
// Used by scraping_test.js (admin) and anteprime.js (featured/preview).
// Exposes globals (no module system): constants + pure-render functions.

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
    L2YT: { label: 'L2YT YouTube', class: 'phase-l2yt' },
    L3: { label: 'L3 Utenti', class: 'phase-l3' },
};

// L2YT e' una variante di L2 ristretta a youtube_editorial: i source_type
// restano "youtube_editorial", quindi cadono nel livello L2 per il rendering.
// La label "L2YT" e' preservata dal badge della sessione.
function _normalizePhaseForRender(phaseFilter) {
    return phaseFilter === 'L2YT' ? 'L2' : (phaseFilter || 'all');
}

const ALIMENTAZIONE_LABEL = {
    benzina: 'Benzina', diesel: 'Diesel', gpl: 'GPL', metano: 'Metano',
    elettrico: 'Elettrico',
    ibrido_full: 'Ibrido Full', ibrido_mild: 'Ibrido Mild', ibrido_plugin: 'Plug-in',
};

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
        types: ['news', 'perplexity', 'youtube_editorial'],
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
    return 'L3';
}

// Utilities --------------------------------------------------------------

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
    div.textContent = text == null ? '' : text;
    return div.innerHTML;
}

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
    const phaseFilter = _normalizePhaseForRender(data.phase_filter);
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
    setTimeout(() => {
        const toggle = banner.querySelector('#show-non-matches');
        if (toggle) {
            toggle.addEventListener('change', () => {
                document.body.classList.toggle('show-non-matches', toggle.checked);
            });
        }
    }, 0);
    return banner;
}

// Rendering --------------------------------------------------------------

function renderResultsInto(container, data, fromSession = false) {
    container.innerHTML = '';

    // Motore filter banner (if filter was requested)
    const hasMotoreFilter = data.filter_alimentazione || data.filter_cilindrata != null;
    if (hasMotoreFilter) {
        const banner = buildMotoreFilterBanner(data);
        if (banner) container.appendChild(banner);
    }

    // Group sources by level
    const grouped = {};
    for (const level of LEVELS) grouped[level.key] = [];
    for (const source of (data.sources || [])) {
        grouped[getLevel(source.source_type)].push(source);
    }

    const brandName = data.brand || '';
    const phaseFilter = _normalizePhaseForRender(data.phase_filter);

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

        const desc = document.createElement('div');
        desc.className = 'level-description';
        desc.textContent = level.description;
        section.appendChild(desc);

        const body = document.createElement('div');
        body.className = 'level-body';

        // L2 minireport: card consolidata in cima alla sezione media/giornalisti.
        // Generato a fine sessione (1 chiamata Claude su tutti gli articoli L2).
        if (level.key === 'L2' && data.l2_synthesis && typeof data.l2_synthesis === 'object') {
            const synthCard = renderL2Synthesis(data.l2_synthesis);
            if (synthCard) body.appendChild(synthCard);
        }

        // L3 minireport: card consolidata in cima alla sezione commenti utenti.
        // Aggrega forum/yt user/reddit + cross-import dei commenti dei video editoriali L2.
        if (level.key === 'L3' && data.l3_synthesis && typeof data.l3_synthesis === 'object') {
            const synthCard = renderL3Synthesis(data.l3_synthesis);
            if (synthCard) body.appendChild(synthCard);
        }

        for (const source of sources) {
            body.appendChild(createSourceCard(source, brandName));
        }
        section.appendChild(body);

        container.appendChild(section);
    }
}

function renderL2Synthesis(synth) {
    if (!synth || !synth.is_l2_synthesis) return null;
    const tono = synth.tono_commenti_utenti || {};
    const forza = Array.isArray(synth.giornalisti_punti_forza) ? synth.giornalisti_punti_forza : [];
    const debolezza = Array.isArray(synth.giornalisti_punti_debolezza) ? synth.giornalisti_punti_debolezza : [];

    const card = document.createElement('div');
    card.className = 'source-card l2-synthesis-card';

    const sentiment = (tono.sentiment_dominante || 'neutro').toLowerCase();
    const sentimentClass = ['positivo', 'neutro', 'misto', 'critico'].includes(sentiment) ? sentiment : 'neutro';

    const buildList = (items) => {
        if (!items.length) return '<p class="synth-empty">Nessun tema ricorrente individuato nel pacchetto.</p>';
        return '<ul class="synth-themes">' + items.map(t => {
            const fonti = Array.isArray(t.fonti) ? t.fonti : [];
            const fontiHtml = fonti.length
                ? `<div class="synth-fonti">Fonti: ${fonti.map(f => `<a href="${escapeHtml(f)}" target="_blank" rel="noopener">${escapeHtml(shortenUrl(f))}</a>`).join(', ')}</div>`
                : '';
            return `<li>
                <div class="synth-tema">${escapeHtml(t.tema || '')}</div>
                <div class="synth-descr">${escapeHtml(t.descrizione || '')}</div>
                ${fontiHtml}
            </li>`;
        }).join('') + '</ul>';
    };

    const note = synth.note_metodologiche
        ? `<div class="synth-note"><strong>Note metodologiche:</strong> ${escapeHtml(synth.note_metodologiche)}</div>`
        : '';

    card.innerHTML = `
        <div class="source-header">
            <div class="source-title">
                <span class="source-icon">📝</span>
                <h3>Minireport L2 — Sintesi media e giornalisti</h3>
                <span class="status-badge status-ok">Sintesi AI</span>
            </div>
        </div>
        <div class="l2-synth-body">
            <div class="synth-section">
                <h4>Tono dei commenti utenti</h4>
                <div class="synth-tono">
                    <span class="synth-sentiment-badge sentiment-${sentimentClass}">${escapeHtml(tono.sentiment_dominante || 'neutro')}</span>
                    <span class="synth-comment-count">${tono.n_commenti_analizzati || 0} commenti analizzati</span>
                </div>
                <p class="synth-descr">${escapeHtml(tono.descrizione || '')}</p>
            </div>
            <div class="synth-section">
                <h4>Punti di forza secondo i giornalisti</h4>
                ${buildList(forza)}
            </div>
            <div class="synth-section">
                <h4>Punti di debolezza secondo i giornalisti</h4>
                ${buildList(debolezza)}
            </div>
            ${note}
        </div>
    `;
    return card;
}

function renderL3Synthesis(synth) {
    if (!synth || !synth.is_l3_synthesis) return null;
    const sent = synth.sentiment_globale || {};
    const apprezzamenti = Array.isArray(synth.apprezzamenti_utenti) ? synth.apprezzamenti_utenti : [];
    const critiche = Array.isArray(synth.critiche_problematiche) ? synth.critiche_problematiche : [];
    const driver = Array.isArray(synth.driver_acquisto) ? synth.driver_acquisto : [];
    const domande = Array.isArray(synth.domande_ricorrenti) ? synth.domande_ricorrenti : [];
    const fontiPerTipo = synth.fonti_per_tipo && typeof synth.fonti_per_tipo === 'object' ? synth.fonti_per_tipo : {};

    const card = document.createElement('div');
    card.className = 'source-card l3-synthesis-card';

    const sentiment = (sent.dominante || 'neutro').toLowerCase();
    const sentimentClass = ['positivo', 'neutro', 'misto', 'critico'].includes(sentiment) ? sentiment : 'neutro';

    const buildThemeList = (items) => {
        if (!items.length) return '<p class="synth-empty">Nessun tema ricorrente individuato nel pacchetto.</p>';
        return '<ul class="synth-themes">' + items.map(t => {
            const fonti = Array.isArray(t.fonti) ? t.fonti : [];
            const fontiHtml = fonti.length
                ? `<div class="synth-fonti">Fonti: ${fonti.map(f => `<a href="${escapeHtml(f)}" target="_blank" rel="noopener">${escapeHtml(shortenUrl(f))}</a>`).join(', ')}</div>`
                : '';
            return `<li>
                <div class="synth-tema">${escapeHtml(t.tema || '')}</div>
                <div class="synth-descr">${escapeHtml(t.descrizione || '')}</div>
                ${fontiHtml}
            </li>`;
        }).join('') + '</ul>';
    };

    const buildDriverList = (items) => {
        if (!items.length) return '<p class="synth-empty">Nessun driver di acquisto ricorrente individuato.</p>';
        return '<ul class="synth-themes">' + items.map(d => {
            const dir = (d.direzione || '').toLowerCase();
            const dirClass = dir === 'pro' ? 'driver-pro' : (dir === 'contro' ? 'driver-contro' : '');
            const dirLabel = dir === 'pro' ? 'Pro' : (dir === 'contro' ? 'Contro' : (d.direzione || ''));
            return `<li>
                <div class="synth-tema">
                    ${escapeHtml(d.driver || '')}
                    ${dirLabel ? `<span class="driver-direction ${dirClass}">${escapeHtml(dirLabel)}</span>` : ''}
                </div>
                <div class="synth-descr">${escapeHtml(d.descrizione || '')}</div>
            </li>`;
        }).join('') + '</ul>';
    };

    const buildQuestionList = (items) => {
        if (!items.length) return '<p class="synth-empty">Nessuna domanda ricorrente individuata.</p>';
        return '<ul class="synth-themes">' + items.map(q => {
            const esempi = Array.isArray(q.esempi) ? q.esempi : [];
            const esempiHtml = esempi.length
                ? `<ul class="synth-questions-examples">${esempi.map(e => `<li>${escapeHtml(e)}</li>`).join('')}</ul>`
                : '';
            return `<li>
                <div class="synth-tema">${escapeHtml(q.tema || '')}</div>
                ${esempiHtml}
            </li>`;
        }).join('') + '</ul>';
    };

    const distrib = sent.distribuzione || {};
    const distribHtml = (distrib.positivi || distrib.neutri || distrib.critici)
        ? `<div class="synth-distrib">
            <span class="distrib-pill sentiment-positivo">${distrib.positivi || 0} positivi</span>
            <span class="distrib-pill sentiment-neutro">${distrib.neutri || 0} neutri</span>
            <span class="distrib-pill sentiment-critico">${distrib.critici || 0} critici</span>
          </div>`
        : '';

    const fontiPillsHtml = Object.keys(fontiPerTipo).length
        ? '<div class="synth-fonti-tipo">' + Object.entries(fontiPerTipo).map(([k, v]) =>
            `<span class="fonte-pill fonte-${escapeHtml(k)}">${escapeHtml(k)}: ${v}</span>`
          ).join('') + '</div>'
        : '';

    const note = synth.note_metodologiche
        ? `<div class="synth-note"><strong>Note metodologiche:</strong> ${escapeHtml(synth.note_metodologiche)}</div>`
        : '';

    card.innerHTML = `
        <div class="source-header">
            <div class="source-title">
                <span class="source-icon">💬</span>
                <h3>Minireport L3 — Sintesi voce utenti</h3>
                <span class="status-badge status-ok">Sintesi AI</span>
            </div>
        </div>
        <div class="l3-synth-body">
            <div class="synth-section">
                <h4>Sentiment globale</h4>
                <div class="synth-tono">
                    <span class="synth-sentiment-badge sentiment-${sentimentClass}">${escapeHtml(sent.dominante || 'neutro')}</span>
                    <span class="synth-comment-count">${sent.n_commenti_analizzati || 0} commenti analizzati</span>
                </div>
                ${distribHtml}
                <p class="synth-descr">${escapeHtml(sent.descrizione || '')}</p>
                ${fontiPillsHtml}
            </div>
            <div class="synth-section">
                <h4>Cosa apprezzano gli utenti</h4>
                ${buildThemeList(apprezzamenti)}
            </div>
            <div class="synth-section">
                <h4>Critiche e problematiche segnalate</h4>
                ${buildThemeList(critiche)}
            </div>
            <div class="synth-section">
                <h4>Driver di acquisto</h4>
                ${buildDriverList(driver)}
            </div>
            <div class="synth-section">
                <h4>Domande ricorrenti</h4>
                ${buildQuestionList(domande)}
            </div>
            ${note}
        </div>
    `;
    return card;
}

function shortenUrl(url) {
    try {
        const u = new URL(url);
        return u.hostname.replace(/^www\./, '') + (u.pathname.length > 30 ? u.pathname.slice(0, 30) + '...' : u.pathname);
    } catch {
        return (url || '').slice(0, 60);
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
                ${renderOfficialInfo(primaryItem.ai_official_info, restItems)}
            `;
            card.appendChild(primary);
        }

        if (restItems.length > 0) {
            if (primaryItem) {
                const fonti = document.createElement('details');
                fonti.className = 'source-fonti';
                const summary = document.createElement('summary');
                summary.innerHTML = `<span class="fonti-label">Fonti analizzate</span> <span class="fonti-count">${restItems.length}</span>`;
                fonti.appendChild(summary);

                const itemsList = document.createElement('div');
                itemsList.className = 'source-items';
                for (const item of restItems) {
                    const itemEl = createResultItem(item, source.source);
                    if (item.matches_filter === false) itemEl.classList.add('non-match');
                    itemsList.appendChild(itemEl);
                }
                fonti.appendChild(itemsList);
                card.appendChild(fonti);
            } else {
                const itemsList = document.createElement('div');
                itemsList.className = 'source-items';
                for (const item of restItems) {
                    const itemEl = createResultItem(item, source.source);
                    if (item.matches_filter === false) itemEl.classList.add('non-match');
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

    let summaryHtml = '';
    if (item.summary) {
        summaryHtml = `<div class="item-summary">${escapeHtml(item.summary)}</div>`;
    }

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
    else if (item.ai_official_info) {
        badges += `<span class="scrape-badge official">L1 Comunicazione ufficiale</span>`;
        contentHtml = renderOfficialInfo(item.ai_official_info);
        if (item.ai_official_info.fonte_consolidata && item.content) {
            contentHtml += `<details class="official-fulltext">
                <summary>Testo sintesi completo</summary>
                <pre>${escapeHtml(item.content)}</pre>
            </details>`;
        }
    }
    else if (item.ai_comments && item.ai_comments.length > 0) {
        contentHtml = renderAiComments(item.ai_comments);
    }
    else if (item.comments && item.comments.length > 0) {
        if (item.channel) {
            subtitle = `${item.channel} \u00B7 ${formatNumber(item.view_count)} views \u00B7 ${formatNumber(item.like_count)} likes`;
        }
        const commentsText = item.comments.map(c => `\uD83D\uDCAC ${c}`).join('\n\n');
        contentHtml = `<pre>${escapeHtml((item.content || '') + '\n\n\u2501\u2501\u2501 Commenti (' + item.comments.length + ') \u2501\u2501\u2501\n\n' + commentsText)}</pre>`;
    }
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

// Aggrega prestazioni / consumi / dimensioni dagli items L1 sito brand (le pagine
// non-driver-analysis) per alimentare l'evidence-block della card "Prestazioni &
// Piacere di guida". Dedup per (versione, alimentazione, cilindrata_cc): pagine
// diverse del sito brand possono ripetere la stessa versione, evitiamo doppioni.
function _collectPerformanceEvidence(items) {
    const versioniMap = new Map();
    const consumiMap = new Map();
    let pesoKg = null;
    let autonomiaMaxKm = null;
    for (const item of (items || [])) {
        const oi = item.ai_official_info || item.official_info || {};
        for (const p of (oi.prestazioni_per_versione || [])) {
            const k = `${p.versione || ''}|${p.alimentazione || ''}|${p.cilindrata_cc || ''}`;
            const hasNumbers = p.cv != null || p.kw != null || p.coppia_nm != null
                || p.zero_cento_s != null || p.velocita_max_kmh != null;
            if (hasNumbers && !versioniMap.has(k)) versioniMap.set(k, p);
        }
        for (const c of (oi.consumi_per_versione || [])) {
            const k = c.versione || '';
            if (!consumiMap.has(k)) consumiMap.set(k, c);
            if (c.autonomia_elettrica_km != null) {
                autonomiaMaxKm = Math.max(autonomiaMaxKm ?? 0, c.autonomia_elettrica_km);
            }
        }
        const dim = oi.dimensioni || {};
        if (pesoKg == null && dim.peso_kg != null) pesoKg = dim.peso_kg;
    }
    return {
        versioni: [...versioniMap.values()],
        consumi: [...consumiMap.values()],
        pesoKg,
        autonomiaMaxKm,
    };
}

function _renderPerformanceEvidence(items) {
    const evi = _collectPerformanceEvidence(items);
    if (!evi.versioni.length && evi.pesoKg == null && evi.autonomiaMaxKm == null) {
        return '';
    }
    let html = `<div class="driver-card-perf-evidence">
        <div class="driver-card-perf-title">Numeri-chiave (dal sito brand)</div>`;
    if (evi.versioni.length > 0) {
        html += `<table class="driver-card-perf-table"><thead><tr>
            <th>Versione</th><th>CV</th><th>kW</th><th>Nm</th><th>0-100</th><th>V.max</th>
            </tr></thead><tbody>`;
        for (const v of evi.versioni) {
            html += `<tr>
                <td>${escapeHtml(v.versione || '—')}</td>
                <td>${v.cv ?? '—'}</td>
                <td>${v.kw ?? '—'}</td>
                <td>${v.coppia_nm ?? '—'}</td>
                <td>${v.zero_cento_s != null ? v.zero_cento_s + ' s' : '—'}</td>
                <td>${v.velocita_max_kmh != null ? v.velocita_max_kmh + ' km/h' : '—'}</td>
            </tr>`;
        }
        html += `</tbody></table>`;
    }
    const extras = [];
    if (evi.pesoKg != null) extras.push(`<span><strong>Peso:</strong> ${evi.pesoKg} kg</span>`);
    if (evi.autonomiaMaxKm != null) extras.push(`<span><strong>Autonomia WLTP:</strong> ${evi.autonomiaMaxKm} km</span>`);
    const cvMax = evi.versioni.reduce((m, v) => Math.max(m, v.cv || 0), 0);
    if (evi.pesoKg != null && cvMax > 0) {
        extras.push(`<span><strong>Peso/potenza:</strong> ${(evi.pesoKg / cvMax).toFixed(1)} kg/CV</span>`);
    }
    if (extras.length > 0) {
        html += `<div class="driver-card-perf-extras">${extras.join(' &middot; ')}</div>`;
    }
    html += `</div>`;
    return html;
}

function renderDriverAnalysis(info, items = []) {
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
            if (d.driver === 'prestazioni_guida') {
                html += _renderPerformanceEvidence(items);
            }
            html += `</div>`;
        }
        html += `</div>`;
    }

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

function renderAggregateOfficial(info) {
    const fmtEUR = (v) => v == null ? null : formatCurrency(v);
    let html = '<div class="official-info aggregate">';

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

    // (Legacy aggregate renderer kept for compatibility with L1_LEGACY_AGGREGATE flag,
    // not actively used in Phase A driver-analysis mode. Short form sufficient for now.)

    html += '</div>';
    return html;
}

function renderOfficialInfo(info, items = []) {
    if (info.is_driver_analysis) return renderDriverAnalysis(info, items);
    if (info.is_aggregate) return renderAggregateOfficial(info);
    // Fallback: empty shell (legacy per-item official_info shape is handled in scraping_test.js)
    return `<div class="official-info"><pre>${escapeHtml(JSON.stringify(info, null, 2))}</pre></div>`;
}
