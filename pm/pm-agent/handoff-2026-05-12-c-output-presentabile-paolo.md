# Handoff: Output presentabile per call Paolo (14/5 h15:30)

**Data:** 2026-05-12
**Da:** PM AI
**A:** Claude Code
**Priorità:** P1
**Stima rough:** S-M (dipende dallo stato attuale di "Anteprima")
**Stato:** ❌ **CANCELLATO 2026-05-13** — vedi nota in cima

---

## ❌ Cancellazione (2026-05-13)

Handoff cancellato da Ale: la sezione "Anteprime" su
`https://unicab.automica.it` **esiste già** ed è esattamente
l'interfaccia di consultazione attesa (lista sessioni di scraping con
filtri motore, minireport L2/L3 espandibili, già usata per le demo
screen-sharing con Paolo). I minireport prodotti dal nuovo flusso
**L2YT** (handoff `b`) confluiranno automaticamente in Anteprime
come quelli L2 standard, senza lavoro UI dedicato.

**Azione per Code:** non eseguire questo handoff. Spostalo in
`pm/pm-agent/handoff-archive/` al prossimo push con commit prefix
`chore(pm): archive handoff-c cancellato`.

---

## Contesto

Call Paolo confermata giovedì 14/5 alle 15:30. Ale farà demo live su
`https://unicab.automica.it` (sezione "Anteprima"). Serve che ciò
che esce dagli handoff `a` (L3 ground truth) e `b` (test solo
YouTube) sia **navigabile in UI da Paolo** senza che Ale debba
mostrare query DB o terminali.

Questo handoff dipende dall'output di `b` (e in misura minore `a`).
Da fare **dopo** che il test solo YouTube ha prodotto risultati.

## Obiettivo

I 2 minireport a confronto (L2 completo vs L2 solo YouTube) prodotti
in handoff `b` sono visibili e leggibili in "Anteprima" della
piattaforma, identificati chiaramente, accessibili al login di
Paolo (`p.brunetti@excellgo.com`).

## Acceptance Criteria

- [ ] In "Anteprima" sono visibili i due minireport (A: L2 completo,
      B: L2 solo YouTube) sullo stesso modello, etichettati in modo
      chiaro ("L2 completo" vs "L2 solo YouTube")
- [ ] Se sono stati testati 2 modelli (vedi handoff `b`), entrambi
      sono in anteprima
- [ ] Login Paolo (`p.brunetti@excellgo.com` / pwd corrente) accede
      e vede i nuovi minireport
- [ ] **Bonus se rapido:** in "Anteprima" è visibile anche un
      mini-indicatore di stato L3 sui modelli testati (es. "commenti
      analizzati: N") — solo se l'handoff `a` ha confermato che i
      dati ci sono e l'aggiunta è banale

## File coinvolti (sospetti)

- `frontend/` (template/static area "Anteprima")
- `backend/app/` endpoint che alimenta "Anteprima"

## Vincoli / non-goals

- **Niente refactor UI.** Solo rendere visibili i risultati nuovi.
- Niente nuove feature di esplorazione (filtri avanzati, export, ecc.):
  obiettivo è la call di giovedì, non un'iterazione di prodotto.
- Se la sezione "Anteprima" già supporta minireport multipli per
  modello in modo banale → semplicemente aggiungi i due nuovi. Se
  invece serve lavoro di UI non banale → fermati, scrivi in FEEDBACK,
  decidiamo se accontentarci di mostrarli "raw" (markdown/PDF
  scaricabile linkato) per la call e rinviare l'UI a dopo.

## Note

- Verifica preventiva utile: aprire `https://unicab.automica.it` con
  login Paolo e capire come sono attualmente esposti i minireport L1/
  L2 in "Anteprima", così l'aggiunta segue lo stesso pattern.
- Ale presenta in screen-sharing: la priorità è che a vista si capisca
  il confronto. Etichette grandi e chiare > eleganza.

---

## 📤 Esito (da compilare da Claude Code a fine task)

**Esito:** ✅ / ❌
**Cosa è stato fatto:**
- ...

**File modificati:**
- ...

**Commit:** `<hash>` _o_ "non committato, vedi diff"

**Note per il PM:**
- ...

**Follow-up emersi:**
- ...
