# Handoff: rotazione credentials + cleanup repo (`Docs/Credentials.txt`)

**Data:** 2026-05-10
**Da:** PM AI
**A:** Claude Code
**Priorità:** **P0 (urgente)**
**Stima rough:** M (1-4h)
**Stato:** 🆕 Nuovo

---

## Contesto

Il file `Docs/Credentials.txt` contiene **6 secret in chiaro** committati nel repo:

1. Firecrawl API key
2. Anthropic Claude API key
3. YouTube Data API v3 key
4. **Perplexity API key** (vedi nota a parte: la nota in `pm/projects/00-stato-progetto.md` "in attesa API key cliente" è **stale**, la key c'è ed è in uso in L1 Strato B)
5. OpenAI API key
6. Webshare proxy (username + password)

Il repo è privato (`mialarussa-hub/unicab-report-automotive`), il rischio è quindi limitato ma non zero. **Pino Iacopino non ha accesso al repo** (informazione utile per dimensionare il blast radius).

Inoltre, la `Proposta Infrastruttura` del 27/3/2026 (vedi `pm/sources/2026-03-27-doc-proposta-infrastruttura.md`) garantisce esplicitamente al cliente:

> *"Tutte le API key gestite come variabili d'ambiente cifrate. Nessuna credenziale in chiaro su filesystem o nei repository."*

→ `Docs/Credentials.txt` viola questa promessa **contrattualmente**, non solo come best practice.

## Obiettivo

Nessun segreto nel repo (HEAD né history), tutte le chiavi ruotate, credenziali caricate via `.env` (in `.gitignore`) o secret manager.

## Acceptance Criteria

- [ ] `git log --follow Docs/Credentials.txt` riportato a inizio task per documentare da quanto tempo il file è committato (input per dimensionare il rischio: rotazione manuale di chiavi nei dashboard provider)
- [ ] **Tutte le 6 chiavi ruotate** lato provider (revoke vecchie + reissue nuove):
  - [ ] Firecrawl (dashboard)
  - [ ] Anthropic Claude (console.anthropic.com)
  - [ ] YouTube Data API v3 (Google Cloud Console)
  - [ ] Perplexity (dashboard) — **verificare in `backend/scrapers/` o nei flussi L1 dove è usata; non assumere che sia inattiva**
  - [ ] OpenAI (dashboard) — capire **se davvero è usata in produzione** (mailing/Whisper? L1?), se no semplicemente revoke senza reissue
  - [ ] Webshare (dashboard proxy) — rigenera credenziali
- [ ] `Docs/Credentials.txt` rimosso da HEAD (`git rm Docs/Credentials.txt`)
- [ ] **Pulizia history**: `git filter-repo --path Docs/Credentials.txt --invert-paths` (o BFG `--delete-files Credentials.txt`). Push forzato dopo aver avvisato Ale (force-push riscrive history, breaking per chiunque abbia clonato).
- [ ] `.gitignore` aggiornato con pattern aggressivo:
  ```
  # Secret files — never commit
  **/Credentials*
  **/credentials*
  *.env
  !.env.example
  *.secret
  ```
- [ ] Le 6 chiavi nuove caricate in `.env` (server prod + locale Ale). Verificare che `pydantic-settings` / dotenv carichi correttamente.
- [ ] `.env.example` aggiornato con i nomi delle chiavi (senza valori).
- [ ] **Aggiorna `pm/ops/CREDENTIALS.md`** con i nuovi "dove" (tabella già scaffoldata, riempi le righe `_da definire post-rotazione_`)

## Verifiche specifiche (riportare in FEEDBACK)

- [ ] **Perplexity usata in main?** Grep su `PERPLEXITY_API_KEY`, `perplexity`, `pplx-`, `sonar` in `backend/scrapers/`. Se sì → conferma in FEEDBACK e correggi nota in `pm/projects/00-stato-progetto.md` ("standby" → "attiva in L1 Strato B"). Se no → conferma, e Perplexity può essere semplicemente revoke + remove key.
- [ ] **OpenAI usata?** Grep per `OPENAI_API_KEY`, `openai`, `gpt-`, `sk-proj-`. Se non usata → revoke senza reissue.
- [ ] **Login demo Paolo** (`p.brunetti@excellgo.com` / `Unicab`): è stata condivisa via mail in chiaro. Da rivalutare con Ale (rotazione + canale sicuro per la consegna? 1Password share, Signal, ecc.). Non urgente quanto le API key ma da chiudere.

## File coinvolti (sospetti)

- `Docs/Credentials.txt` (da rimuovere)
- `.gitignore`
- `.env`, `.env.example`
- `backend/app/core/config.py` o equivalente (per verifica dotenv/pydantic-settings)
- `pm/ops/CREDENTIALS.md` (popola tabella)
- `pm/projects/00-stato-progetto.md` (correggi nota su Perplexity se applicabile — vedi anche FEEDBACK del 2026-05-11)

## Vincoli / non-goals

- Non rifattorizzare la gestione config esistente. Solo sostituire i valori e rimuovere il file in chiaro.
- Non toccare il codice dei flussi L1/L2/L3 a parte i punti di lettura della chiave.
- **Non fare push forzato senza avvisare Ale** — la riscrittura della history è destructive per ogni clone esistente.

## Note

- Il PM ha già messo questo handoff in `pm/SPRINT.md` come P0.
- Eventuali sorprese o dubbi tecnici → `pm/pm-agent/FEEDBACK.md` (canale bidirezionale).
- Una volta chiuso, archivia questo file in `pm/pm-agent/handoff-archive/`.

---

## 📤 Esito (da compilare da Claude Code a fine task)

**Esito:** ✅ / ❌
**Cosa è stato fatto:**
- ...

**File modificati:**
- ...

**Commit:** `<hash>` _o_ "non committato, vedi diff"

**Note per il PM:**
- Perplexity confermata attiva / non attiva?
- OpenAI confermata attiva / non attiva?
- Eventuali altri segreti trovati durante la pulizia che non erano in `Credentials.txt`?

**Follow-up emersi:**
- ...
