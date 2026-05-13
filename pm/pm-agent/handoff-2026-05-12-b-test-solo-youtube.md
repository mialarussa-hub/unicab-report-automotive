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

Produrre, per 1-2 modelli auto, **due minireport a confronto** sullo
stesso modello e stesso intervallo temporale:
- A) **L2 completo** — YouTube editoriali (4 canali) + 8 testate news
- B) **L2YT** — solo i 4 canali editoriali YouTube

In modo che Ale (e Paolo in call) possano valutare side-by-side cosa
si perde escludendo le testate scritte.

## Requisito strutturale (decisione Ale 2026-05-13)

**L2YT non è un test one-shot, è un flusso permanente.** Va
introdotto come **secondo flusso parallelo a L2** (filtro/variante
`L2YT`), in modo che resti nel sistema dopo la call e possa essere
rilanciato in futuro per confronti su altri modelli senza dover
rifare patch temporanee.

Il flusso L2 standard (8 testate + 4 YouTube) **non si tocca e non si
disabilita** — continua a esistere com'è. Si aggiunge L2YT come
variante selezionabile, in parallelo.

Naming convenzionale: **`L2YT`** (es. come `source_type`, label UI,
chiave config, etichetta minireport — usare la stessa sigla ovunque
per leggibilità).

## Acceptance Criteria

- [ ] **L2YT esiste come flusso parallelo a L2**, selezionabile dal
      sistema (non è un branch temporaneo né un flag locale "una
      tantum"). Il flusso L2 standard resta intatto.
- [ ] Scelti 1-2 modelli auto rappresentativi (suggerimento: uno mass
      market + uno premium, oppure due segmenti diversi — proporre a
      PM/Ale prima di lanciare lo scrape se non ovvio)
- [ ] Ingestion completata per entrambi i flussi (L2 e L2YT) sullo
      stesso modello e intervallo temporale, con dati salvati in DB
      e tracciabili (distinguibili per tipo di flusso)
- [ ] Generati i due minireport AI a confronto (sintesi
      media/giornalisti per L2; sintesi solo YouTube per L2YT)
- [ ] Output **accessibile** ad Ale prima della call: visibile
      nell'area "Anteprime" della piattaforma
      (`https://unicab.automica.it`). La sezione esiste già e mostra
      le sessioni di scraping con minireport L2/L3 — il flusso L2YT
      deve confluire lì come gli altri (etichetta chiara `L2YT` vs
      `L2`)
- [ ] Riportato in `pm/pm-agent/FEEDBACK.md` un breve riepilogo
      tecnico: modelli scelti, intervallo, dove guardare i risultati,
      come si lancia un L2YT in futuro, eventuali anomalie

## File coinvolti (sospetti)

- `scrapers/src/test_scrape.py` (qui ci sono `YOUTUBE_EDITORIAL_CHANNELS`
  e `NEWS_MOTORI_DOMAINS`, suggerisce sia il punto di entrata)
- `scrapers/src/perplexity_client.py` (non rilevante per L2, segnalo
  solo per non confondersi: L2 non usa Perplexity)
- Pipeline report AI (path da verificare in `backend/`)

## Vincoli / non-goals

- **Non rimuovere/disabilitare le testate news dal codice.** L2YT
  affianca L2, non lo sostituisce. L2 standard deve continuare a
  funzionare identico.
- **Non improvvisare il naming.** Usare `L2YT` come sigla unica per
  source_type, label UI, chiave config, etichetta minireport. Se
  l'architettura impone una variante (es. `l2_yt`, `l2-yt`), ok
  pragmaticamente — ma una sola variante, coerente ovunque.
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
