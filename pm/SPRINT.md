# 🏃 SPRINT corrente

**Sprint:** 19-20 (2 settimane)
**Inizio sprint:** 2026-05-11
**Fine sprint prevista:** 2026-05-24

---

## Task

| Priorità | Task | Stato | Note |
|---|---|---|---|
| P0 | Verifica + completamento **L3 commenti** | ⏳ | Ground truth + stima residua per call Paolo 14/5 → pm/pm-agent/handoff-2026-05-12-a-l3-ground-truth.md |
| P0 | Test **"solo YouTube"** vs L2 completo | ⏳ | Confronto side-by-side per scope decision con Paolo in call 14/5 → pm/pm-agent/handoff-2026-05-12-b-test-solo-youtube.md |
| P0 | **L4 campagne adv** — approfondire bozza | ⏳ | Esiste solo una bozza, va approfondita prima di passare a Code. Task di disegno (Ale): scope, fonti (Facebook Ads Library + Google Ads), output atteso, integrazione con L2/L3. Da L4 disegnato → handoff esecuzione. Da preparare per call 14/5. |
| P1 | Output presentabile call Paolo (Anteprima UI) | ⏳ | Rendere navigabili in "Anteprima" i 2 minireport prodotti dal test solo YouTube → pm/pm-agent/handoff-2026-05-12-c-output-presentabile-paolo.md |
| P1 | Scheda **"Prestazioni"** in L1 + verifica Heritage / Lifestyle | ⏳ | Promozione di 3 driver "non comunicati" a card visibili + numeri-chiave prestazionali come evidence → pm/pm-agent/handoff-2026-05-12-d-scheda-prestazioni-l1.md |
| P1 | _(triggered)_ Strutturare dataset prototipo | ⏸️ | Bloccato finché Paolo non manda numero auto (ipotesi 500-1000 modello+versione, da ridurre a pochi segmenti). |
| P2 | _(triggered)_ Integrare 4° ibrido (Extended Range) | ⏸️ | **Declassato a P2 (2026-05-11):** è questione di sola nomenclatura, non un tema operativo. Bloccato finché Paolo non conferma nome esatto + modelli (Nissan/BYD), ma senza urgenza. |
| P2 | ADR retroattivi: architettura 4-layer + scope Release 0.0 | ⏳ | Documentare scelte già prese in `pm/decisions/`. Utile perché stiamo costruendo il prototipo su queste fondamenta. |
| P2 | ~~Riattivazione **Perplexity (Sonar)**~~ | ❌ | **Cancellato 2026-05-11.** Premessa errata: Perplexity Sonar Pro è già attiva in L1 Strato B (`scrapers/src/perplexity_client.py` + `_scrape_official_perplexity` in `test_scrape.py:1667`). La nota "in attesa API key cliente" in `00-stato-progetto.md` era stale, corretta da Code (commit `chore(pm): risposta a discrepanze FEEDBACK + correzioni 00-stato-progetto`). Esiste un dispatch legacy `source_type="perplexity"` mappato a L2 con UI nascosta, materiale legacy. |
| P2 | Aggiungere `pm/sources/` a `.gitignore` | ✅ | Chiuso 2026-05-10. Vedi handoff archiviato → `pm/pm-agent/handoff-archive/handoff-2026-05-10-a-gitignore-pm-sources.md` |

**Legenda priorità**
- **P0** — Bloccante / urgente, va fatto subito
- **P1** — Importante, da chiudere entro lo sprint
- **P2** — Nice to have, opzionale

**Legenda stato**
- ⏳ Da fare
- 🔄 In corso
- ⏸️ In attesa (blocco esterno)
- ✅ Fatto
- ❌ Cancellato

**Convenzione note**
- Per task piccoli (1-2 step): descrizione inline qui
- Per task complessi: link a handoff `→ pm/pm-agent/handoff-YYYY-MM-DD-x-topic.md`

---

## Note sprint corrente

**Goal sprint:** chiudere L3, capire scope L2 finale (test "solo YouTube"), passare a L4 con piano operativo (non più solo bozza). Il prototipo "numero zero" deve avere L2+L3+L4 funzionanti per la Release 0.0 — vedi `pm/projects/release-0-0-prototipo.md`.

**Calendario call Paolo:**
- ✅ **Confermata: giovedì 14/5 alle 15:30** (Paolo conferma via mail 12/5)
- Scaletta concordata con PM: (a) stato L3, (b) test solo YouTube + decisione scope L2, (c) L4 adv bozza, (d) scheda prestazioni L1, (e) pending Paolo (numero modelli prototipo, intestazione fatture)
- Prep call: 3 handoff aperti per Code (12-05 a/b/c), L4 e scheda prestazioni in carico ad Ale come disegno

**Pending Paolo (dalla call 4 maggio + mail 23 aprile):**
- Numero auto prototipo (ipotesi 500-1000 → ridurre a pochi segmenti)
- Decisione fatturazione mensile + soggetto fatturazione (**UNICAB Italia SRL** da contratto, ma Paolo ha proposto società terza, probabile Excellgo — deve sentire il fratello)
- _(minore)_ Conferma nome 4° tipo ibrido (Extended Range) — solo nomenclatura, non urgente

**Sensibilità da tenere a mente:** Paolo ha citato un evento familiare difficile (padre coinvolto nel progetto). Sui solleciti, dare margine. Modello operativo: auto **a gruppetti**, non file unico.

**Riferimenti:**
- Scope prototipo: `pm/projects/release-0-0-prototipo.md`
- Call sintesi: `pm/sources/2026-05-04-call-paolo.md` (locale, gitignored)
