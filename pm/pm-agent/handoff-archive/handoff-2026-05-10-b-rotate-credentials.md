# Handoff: rotazione credentials + cleanup repo (`Docs/Credentials.txt`)

**Data:** 2026-05-10
**Da:** PM AI
**A:** Claude Code
**Priorità:** **P0 (urgente)**
**Stima rough:** M (1-4h)
**Stato:** ❌ Cancellato (decisione utente 2026-05-11 — vedi sezione Esito)

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

## 📤 Esito

**Esito:** ❌ Cancellato dall'utente (decisione 2026-05-11)

**Verifiche tecniche fatte prima della cancellazione:**
- `Docs/Credentials.txt` non è mai stato committato. `git log --all --diff-filter=A -- Docs/Credentials.txt` ritorna vuoto. Il file è già coperto da `.gitignore` (regola `Credentials.txt` originaria, ora rafforzata dai pattern `**/Credentials*` e `**/credentials*`).
- Premessa dell'handoff ("6 secret in chiaro committati nel repo") era errata: i secret sono solo sul filesystem locale di Ale, mai esposti via git.
- Perplexity confermata **attiva** in L1 Strato B (`scrapers/src/perplexity_client.py` + `_scrape_official_perplexity` in `test_scrape.py:1667`).
- OpenAI confermata **attiva** in L2 (`_transcribe_audio_with_whisper` in `test_scrape.py:1394`, Whisper API per audio YouTube editoriale).

**Decisione utente (2026-05-11):**
Ale ha deciso di **mantenere `Docs/Credentials.txt` dov'è**, come scratchpad locale per condividere chiavi API e password con Claude Code durante le sessioni. Il file è già gitignored e non viene committato. Niente rotazione delle 6 chiavi, niente cancellazione del file. La convenzione è documentata in `pm/ops/CREDENTIALS.md` (sezione "Convenzione operativa di Ale").

**Cosa resta in repo dai commit della sessione (utile comunque):**
- `.gitignore` con pattern aggressivi `**/Credentials*`, `**/credentials*`, `*.secret` (commit `6146287`)
- `.env.example` completato con i 6 nomi-chiave finora mancanti (commit `6146287`)
- `pm/ops/CREDENTIALS.md` popolato con l'inventario reale (no rotazione, no placeholder)

**Follow-up emersi (bassa priorità, non urgenti):**
- Login demo Paolo (`p.brunetti@excellgo.com` / `Unicab`): password debole condivisa via mail in chiaro. Scope limitato (solo dashboard demo). Valutare quando opportuno.
