// UNICAB — Sources Management

const TYPE_LABELS = {
    news: { label: 'News / Magazine', icon: '📰' },
    forum: { label: 'Forum', icon: '💬' },
    youtube: { label: 'YouTube', icon: '▶️' },
    social: { label: 'Social', icon: '👥' },
};

// Load sources on page load
document.addEventListener('DOMContentLoaded', loadSources);

// Add source form
document.getElementById('add-source-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('name').value.trim();
    const url = document.getElementById('url').value.trim();
    const source_type = document.getElementById('source_type').value;

    if (!name || !url) return;

    const addBtn = document.getElementById('add-btn');
    addBtn.disabled = true;

    try {
        const resp = await fetch('/api/sources/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ name, url, source_type }),
        });

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        // Reset form and reload
        document.getElementById('add-source-form').reset();
        await loadSources();
    } catch (err) {
        alert('Errore: ' + err.message);
    } finally {
        addBtn.disabled = false;
    }
});

async function loadSources() {
    const container = document.getElementById('sources-list');

    try {
        const resp = await fetch('/api/sources/', {
            credentials: 'same-origin',
        });

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const sources = await resp.json();

        if (sources.length === 0) {
            container.innerHTML = '<p class="empty-state">Nessuna fonte configurata. Aggiungi la prima fonte sopra.</p>';
            return;
        }

        container.innerHTML = '';
        for (const source of sources) {
            container.appendChild(createSourceCard(source));
        }
    } catch (err) {
        container.innerHTML = `<div class="error-banner">Errore caricamento fonti: ${err.message}</div>`;
    }
}

function createSourceCard(source) {
    const typeInfo = TYPE_LABELS[source.source_type] || { label: source.source_type, icon: '📄' };

    const card = document.createElement('div');
    card.className = `source-entry ${source.is_active ? '' : 'inactive'}`;
    card.innerHTML = `
        <div class="source-info">
            <span class="source-type-icon">${typeInfo.icon}</span>
            <div>
                <strong>${escapeHtml(source.name)}</strong>
                <span class="source-type-label">${typeInfo.label}</span>
                <div class="source-url">${escapeHtml(source.url)}</div>
            </div>
        </div>
        <div class="source-actions">
            <button class="btn-toggle ${source.is_active ? 'active' : ''}" onclick="toggleSource('${source.id}')">
                ${source.is_active ? 'Attiva' : 'Disattiva'}
            </button>
            <button class="btn-delete" onclick="deleteSource('${source.id}', '${escapeHtml(source.name)}')">✕</button>
        </div>
    `;
    return card;
}

async function toggleSource(id) {
    try {
        await fetch(`/api/sources/${id}/toggle`, {
            method: 'PATCH',
            credentials: 'same-origin',
        });
        await loadSources();
    } catch (err) {
        alert('Errore: ' + err.message);
    }
}

async function deleteSource(id, name) {
    if (!confirm(`Eliminare la fonte "${name}"?`)) return;

    try {
        await fetch(`/api/sources/${id}`, {
            method: 'DELETE',
            credentials: 'same-origin',
        });
        await loadSources();
    } catch (err) {
        alert('Errore: ' + err.message);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
