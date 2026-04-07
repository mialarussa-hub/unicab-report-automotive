// UNICAB — Scraping Test Frontend

const SOURCE_LABELS = {
    forums: { name: 'Forum Automotive', icon: '💬' },
    youtube: { name: 'YouTube', icon: '▶️' },
    facebook_ads: { name: 'Facebook Ads', icon: '📢' },
    google_ads: { name: 'Google Ads', icon: '🔍' },
};

const STATUS_LABELS = {
    ok: { label: 'OK', class: 'status-ok' },
    partial: { label: 'Parziale', class: 'status-partial' },
    error: { label: 'Errore', class: 'status-error' },
};

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

    } catch (err) {
        resultsContainer.innerHTML = `<div class="error-banner">Errore: ${err.message}</div>`;
    } finally {
        submitBtn.disabled = false;
        loading.style.display = 'none';
    }
});

function renderResults(data) {
    const resultsContainer = document.getElementById('results');
    const resultsMeta = document.getElementById('results-meta');

    // Meta info
    document.getElementById('meta-credits').textContent = `Credits Firecrawl: ${data.total_credits}`;
    document.getElementById('meta-duration').textContent = `Durata: ${(data.total_duration_ms / 1000).toFixed(1)}s`;
    resultsMeta.style.display = 'flex';

    // Source cards
    resultsContainer.innerHTML = '';
    for (const source of data.sources) {
        const card = createSourceCard(source);
        resultsContainer.appendChild(card);
    }
}

function createSourceCard(source) {
    const info = SOURCE_LABELS[source.source] || { name: source.source, icon: '📄' };
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
    let subtitle = '';
    let content = '';

    if (sourceType === 'youtube') {
        subtitle = `${item.channel} · ${formatNumber(item.view_count)} views · ${formatNumber(item.like_count)} likes`;
        content = item.description || '';
        if (item.comments && item.comments.length > 0) {
            content += '\n\n--- Commenti ---\n' + item.comments.map((c, i) => `${i + 1}. ${c}`).join('\n');
        }
    } else {
        subtitle = item.url || '';
        content = item.content || '';
    }

    const isPriority = item.is_priority ? '<span class="priority-badge">Forum noto</span>' : '';

    el.innerHTML = `
        <div class="item-header" onclick="this.parentElement.classList.toggle('expanded')">
            <strong>${escapeHtml(title)}</strong> ${isPriority}
            <span class="expand-icon">▼</span>
        </div>
        <div class="item-subtitle">${escapeHtml(subtitle)}</div>
        <div class="item-content"><pre>${escapeHtml(content)}</pre></div>
    `;

    return el;
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
