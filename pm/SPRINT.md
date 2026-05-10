# 🏃 SPRINT corrente

**Sprint:** 19-20 (2 settimane)
**Inizio sprint:** 2026-05-11
**Fine sprint prevista:** 2026-05-24

---

## Task

| Priorità | Task | Stato | Note |
|---|---|---|---|
| P0 | Verifica + completamento **L3 commenti** | ⏳ | Stima ~8h+. Era da chiudere entro 5 maggio (call Paolo), in realtà non è chiuso. [handoff Code] Ground truth: cosa è già live di L3 (sentiment, ingest commenti YouTube/Reddit/forum), cosa manca per chiudere. Riportare in FEEDBACK con stima residua. |
| P0 | Test **"solo YouTube"** vs L2 completo | ⏳ | Verificare se YouTube editoriale da solo è sufficiente per il prototipo, o se servono anche le testate news. Output: decisione di scope L2. [handoff Code] da disegnare quando l'approccio è chiaro. |
| P0 | **L4 campagne adv** — approfondire bozza | ⏳ | Esiste solo una bozza, va approfondita prima di passare a Code. Task di disegno (Ale): scope, fonti (Facebook Ads Library + Google Ads), output atteso, integrazione con L2/L3. Da L4 disegnato → handoff esecuzione. |
| P1 | Scheda **"prestazioni"** in L1 | ⏳ | Preso con Paolo. Test su Honda Jazz e modelli segmento C/D. [handoff Code] dopo che disegno scheda è stato discusso. |
| P1 | _(triggered)_ Strutturare dataset prototipo | ⏸️ | Bloccato finché Paolo non manda numero auto (ipotesi 500-1000 modello+versione, da ridurre a pochi segmenti). |
| P1 | _(triggered)_ Integrare 4° ibrido (Extended Range) | ⏸️ | Bloccato finché Paolo non conferma nome esatto + modelli (Nissan/BYD). |
| P2 | ADR retroattivi: architettura 4-layer + scope Release 0.0 | ⏳ | Documentare scelte già prese in `pm/decisions/`. Utile perché stiamo costruendo il prototipo su queste fondamenta. |
| P2 | Riattivazione **Perplexity (Sonar)** | ⏸️ | UI nascosta, codice in main. In attesa di `PERPLEXITY_API_KEY` cliente. Dipendenza esterna senza ETA. |
| P2 | Aggiungere `pm/sources/` a `.gitignore` | ⏳ | → `pm/pm-agent/handoff-2026-05-10-a-gitignore-pm-sources.md` |

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
- Ale lo sente lun 11-mag per fissare la prossima call
- Probabile finestra mer 13 / gio 14 maggio
- Aggiornamenti al PM via questa chat

**Pending Paolo (dalla call 4 maggio):**
- Numero auto prototipo (ipotesi 500-1000 → ridurre a pochi segmenti)
- Conferma 4° tipo ibrido (Extended Range Hybrid)
- Decisione fatturazione mensile (deve sentire il fratello)

**Sensibilità da tenere a mente:** Paolo ha citato un evento familiare difficile (padre coinvolto nel progetto). Sui solleciti, dare margine. Modello operativo: auto **a gruppetti**, non file unico.

**Riferimenti:**
- Scope prototipo: `pm/projects/release-0-0-prototipo.md`
- Call sintesi: `pm/sources/2026-05-04-call-paolo.md` (locale, gitignored)
