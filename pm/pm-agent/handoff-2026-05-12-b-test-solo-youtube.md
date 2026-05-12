# Handoff: Test "solo YouTube" su L2 — confronto con L2 completo

**Data:** 2026-05-12
**Da:** PM AI
**A:** Claude Code
**Priorità:** P0
**Stima rough:** M (1-4h)
**Stato:** 🆕 Nuovo

---

## Contesto

Nella mail dell'11 maggio Ale ha anticipato a Paolo che avrebbe fatto
"un test solo YouTube sul Layer 2, per capire insieme se i contenuti
dei canali editoriali bastano o se le testate scritte aggiungono
valore reale". In call giovedì 14/5 alle 15:30 Paolo si aspetta di
vedere un primo risultato per decidere insieme lo scope L2 finale.

Questa è probabilmente la cosa più importante da portare alla call:
**decide lo scope L2 del prototipo (Release 0.0)**.

## Obiettivo

Produrre, per 1-2 modelli auto, **due minireport L2 a confronto** sullo
stesso modello e stesso intervallo temporale:
- A) **L2 completo** — YouTube editoriali (4 canali) + 8 testate news
- B) **L2 solo YouTube** — solo i 4 canali editoriali YouTube

In modo che Ale (e Paolo in call) possano valutare side-by-side cosa
si perde escludendo le testate scritte.

## Acceptance Criteria

- [ ] Scelti 1-2 modelli auto rappresentativi (suggerimento: uno mass
      market + uno premium, oppure due segmenti diversi — proporre a
      PM/Ale prima di lanciare lo scrape se non ovvio)
- [ ] Ingestion completata per entrambi i flussi (A e B) sullo stesso
      intervallo temporale, con dati salvati in DB e tracciabili
- [ ] Generati i due minireport AI a confronto (sintesi
      media/giornalisti per A; sintesi solo YouTube per B)
- [ ] Output **accessibile** ad Ale prima della call: idealmente
      visibile nell'area "Anteprima" della piattaforma
      (`https://unicab.automica.it`) → vedi handoff `c` per la parte
      di presentazione UI se serve frontend dedicato
- [ ] Riportato in `pm/pm-agent/FEEDBACK.md` un breve riepilogo
      tecnico: modelli scelti, intervallo, dove guardare i risultati,
      eventuali anomalie

## File coinvolti (sospetti)

- `scrapers/src/test_scrape.py` (qui ci sono `YOUTUBE_EDITORIAL_CHANNELS`
  e `NEWS_MOTORI_DOMAINS`, suggerisce sia il punto di entrata)
- `scrapers/src/perplexity_client.py` (non rilevante per L2, segnalo
  solo per non confondersi: L2 non usa Perplexity)
- Pipeline report AI (path da verificare in `backend/`)

## Vincoli / non-goals

- **Non rimuovere/disabilitare le testate news dal codice.** Il test
  serve a confrontare, non a togliere. Se serve un flag/parametro
  temporaneo per girare solo YouTube, ok; non patchare via.
- Non aprire ADR sullo scope L2 in questo handoff — la decisione la
  prende Ale con Paolo in call e poi eventualmente arriva un nuovo
  handoff "consolidamento scope L2".
- Niente Whisper sui video → assumi che la trascrizione audio dei
  video YouTube ed. sia già parte del flusso L2 standard; non
  forzare ri-trascrizioni se non necessario (costo + tempo).

## Note

- Output deve essere **leggibile da Paolo non-tecnico**: due
  minireport che mostrino chiaramente "questo è cosa dicono i canali
  YouTube ed." vs "questo è cosa aggiungono le 8 testate news".
- Se possibile, includi un piccolo riassunto di delta (es. "le testate
  aggiungono X menzioni in più / argomenti diversi su Y") — anche
  qualitativo va bene per la call.
- Se identifichi che il test richiede modifiche strutturali pesanti
  per essere replicabile, **fermati e segnala in FEEDBACK** prima di
  procedere con scelte fuori scope.

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
