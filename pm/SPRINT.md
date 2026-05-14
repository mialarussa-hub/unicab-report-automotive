# 🏃 SPRINT corrente

**Sprint:** 19-20 (2 settimane)
**Inizio sprint:** 2026-05-11
**Fine sprint prevista:** 2026-05-24

---

## Task

| Priorità | Task | Stato | Note |
|---|---|---|---|
| P0 | Verifica + completamento **L3 commenti** | ✅ | Chiuso 2026-05-12. Minireport L3 implementato e deployato in prod (commit `03a39d8` + `9113e02` + `62ba086`). Filtro semantico target nel prompt L3 propaga alim/cilindrata. Test riuscito su Fiat Grande Panda 1.2 benzina (1048 commenti su 47 thread → 3 apprezzamenti, 5 critiche, 3 driver, 2 domande). **Domani altri test su modelli diversi** per validare robustezza. Handoff archiviato in `handoff-archive/handoff-2026-05-12-a-l3-ground-truth.md`. |
| P0 | Introdurre flusso **L2YT** + confronto con L2 completo | ✅ | Chiuso 2026-05-13. Flusso L2YT implementato come variante permanente di L2 (solo 4 canali YouTube ed., L2 standard intatto). Commit `2cd74fc`. Deployato in prod su `unicab.automica.it` (force-recreate api+scrapers, restart nginx). Selezionabile da UI admin "Test Scraping" → dropdown Fase → "Solo L2YT — YouTube editoriali", oppure POST `/api/scraping-test/run` con `phase: "L2YT"`. Minireport L2 con prompt auto-adattivo (passato `sources_used`: quando contiene solo youtube_editorial, l'introduzione cambia per non citare testate scritte assenti). I 2 modelli di confronto li lancia Ale. Handoff archiviato in `handoff-archive/handoff-2026-05-12-b-test-solo-youtube.md`. |
| P0 | ~~Indagine anomalia L2 vs L2YT (prompt/pipeline)~~ | ❌ | **Cancellato 2026-05-14 post-call**: con decisione Paolo "L2 YouTube-only", L2YT diventa L2 e il delta si annulla per costruzione. Handoff `handoff-2026-05-14-a-anomalia-l2-vs-l2yt-prompt.md` da archiviare da Code senza esecuzione. |
| P0 | ~~L4 campagne adv — approfondire bozza (scope v1)~~ | ❌ | **Superseded 2026-05-14 post-call**: scope v1 (FB Ads + Google + Perplexity trade press) tagliato da Paolo. Sostituito da nuovo task L4 sotto, con scope ridotto. |
| ⏸️ post-standby | **L4 Google Ads — test fattibilità + disegno** | ⏸️ | **Stand-by fino a ripartenza fine maggio.** Nuovo scope post-call Paolo: solo Google Ads, output = (a) n. creatività ultimi 6 mesi, (b) continuità temporale, (c) timeline campagne. NIENTE spend €, messaggio chiave, affissioni. Da testare empiricamente: se timeline troppo onerosa, scope si rinegozia con Paolo. |
| ⏸️ post-standby | **L3 conteggi quantitativi per categoria** | ⏸️ | **Stand-by.** Richiesta esplicita Paolo in call 14/5: senza conteggio, 1 commento sfortunato = pattern diffuso. Aggiungere al minireport L3 misura di quanti commenti ricadono in ogni categoria (sentiment/forza/debolezza). |
| ⏸️ post-standby | **Convergenza L2YT → L2** (rename + archiviazione know-how testate scritte) | ⏸️ | **Stand-by.** Decisione Ale 14/5: rinominiamo L2YT in L2 ma **non buttiamo via** il lavoro su testate scritte (8 testate integrate, prompt 2-step search→scrape, gotchas accumulati). Da decidere con Code come archiviare bene il workflow legacy (branch dedicato? cartella `legacy/`? doc in `pm/decisions/`?). |
| ⏸️ post-standby | **Emissione prima fattura UNICAB** | ⏸️ | **Stand-by, attesa email Paolo** con intestazione "l'altra società". Ale emette fattura con ore svolte finora, pagamento entro fine maggio 2026. Una volta arrivata l'email Paolo: aggiornare intestazione cliente + emettere. |
| P1 | ~~Output presentabile call Paolo (Anteprima UI)~~ | ❌ | **Cancellato 2026-05-13.** Doppione: la sezione "Anteprime" esistente già fa il job (consultabile da Paolo, usata da Ale per demo screen-sharing). I minireport prodotti dal flusso L2YT confluiscono automaticamente in Anteprime come quelli L2. Handoff `handoff-2026-05-12-c-output-presentabile-paolo.md` marcato ❌ Cancellato (Code lo archivierà al prossimo push). |
| P1 | Scheda **"Prestazioni"** in L1 + verifica Heritage / Lifestyle | ✅ | Chiuso 2026-05-13. Card "Prestazioni & Piacere di guida" arricchita con blocco evidence "Numeri-chiave (dal sito brand)" sotto le citazioni: tabella per versione (CV, kW, Nm, 0-100, V.max) + extras (peso curb, autonomia WLTP EV, peso/potenza calcolato). Commit `f907ba5`, deployato in prod (solo restart nginx, frontend ha bind-mount). **Decisione Ale 2026-05-13**: i 3 driver target (Prestazioni, Heritage, Lifestyle) NON sono stati "promossi" a card sempre visibili — Ale ha richiesto «la card prestazioni deve funzionare come le altre card quando le info scarseggiano», quindi tutte le 9 card mantengono il comportamento standard (peso>0 → card, peso=0 → riga "Driver non comunicati" in fondo). Verifica preliminare ontologia: tutte e 9 le categorie già presenti in `DRIVER_TAXONOMY` (`content_cleaner.py:582`), nessun refactor d'ontologia richiesto. Handoff archiviato in `handoff-archive/handoff-2026-05-12-d-scheda-prestazioni-l1.md`. |
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

**🛑 STAND-BY ~2 settimane** dal 2026-05-14 (call Paolo). Riavvio stimato fine maggio / inizio giugno, a discrezione di Paolo. Ale operativo in background (no task pressanti). Goal originale sprint 19-20 superato dalla call.

**Outcome call Paolo 14/5 (15:30 CEST, 33 min):**
- Cliente in stand-by per ragioni personali. Saluti cordiali, fatturazione attivata, rapporto solido.
- **Decisione strategica**: L2/L3/L4 si focalizzano su **YouTube + Google Ads only**. Tagliati Reddit + testate scritte L2 + Perplexity trade press + Facebook Ads Library.
- L4 scope ridotto: 3 metriche (n. creatività 6 mesi, continuità, timeline). No spend €.
- L3 deve diventare quantitativo (conteggi commenti per categoria).
- L1 Prestazioni compilazione condizionale ratificata.
- Bug cap items_text comunicato a Paolo come "onestà tecnica" — chiuso.
- Vedi meeting note: `pm/sources/UNICAB_meeting_2026-05-14.md`.

**Stato task chiusi 2026-05-13:**
- L2YT ✅ (commit `2cd74fc`) — diventerà "L2" tout-court post-stand-by
- Scheda Prestazioni L1 ✅ (commit `f907ba5`, scope ridotto ratificato da Paolo)
- Bug fix cap items_text 80k → 600k ✅ (commit `bcb716d` + `4bcf66c`)
- Anteprima UI ❌ (doppione: Anteprime esisteva già)

**Cancellati post-call 14/5:**
- L4 scope v1 (FB Ads + Google + Perplexity trade press) → sostituito da L4 Google Ads only
- Indagine anomalia L2 vs L2YT → obsoleto con YouTube-only

**Pending Paolo (aggiornato post-call 14/5):**
- 📩 **Intestazione "l'altra società" per fattura** (Paolo manda via email) — sblocca emissione prima fattura
- Numero auto prototipo (dataset immatricolazioni — "ultima cosa" che vuole consolidare)
- Verifica nomenclatura ibridi su dataset Quattroruote (Paolo)
- _(decaduto)_ Conferma nome 4° tipo ibrido: la categoria "ibrido a sola ricarica / generatore termico" entra in stand-by — non si definisce a monte, si gestisce come risultato di ricerca se emerge

**Sensibilità da tenere a mente:** Paolo ha citato di nuovo difficoltà personali in call 14/5 ("non riesco a dedicare l'attenzione necessaria"). Saluti calorosi ("un abbraccione"). Sui solleciti, **massima delicatezza** — è lui che ci riprende per primo.

**Riferimenti:**
- Scope prototipo: `pm/projects/release-0-0-prototipo.md` (da rivedere post-stand-by — scope L2/L3/L4 cambiato)
- Call 14/5 sintesi: `pm/sources/UNICAB_meeting_2026-05-14.md`
- Call 4 maggio: `pm/sources/2026-05-04-call-paolo.md` (locale, gitignored)
- Doc prep call 14/5: `pm/projects/2026-05-14-prep-call-paolo.docx`
