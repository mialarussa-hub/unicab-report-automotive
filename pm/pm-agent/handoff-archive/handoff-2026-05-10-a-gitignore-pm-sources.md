# Handoff: aggiungere `pm/sources/` a `.gitignore`

**Data:** 2026-05-10
**Da:** PM AI
**A:** Claude Code
**Priorità:** P2
**Stima rough:** S (<1h, in pratica <10 min)
**Stato:** ✅ Completato

---

## Contesto

Il PM ha creato una cartella `pm/sources/` come "diario di contesto" che contiene trascrizioni call, mail, note di Paolo. La scelta dell'utente è di **non versionare** questi file in git (anche con repo privata: privacy + igiene del repo). I file devono restare solo sul filesystem locale di Ale.

Non c'è alcuna restrizione di accesso lato Code: Code può leggere `pm/sources/` se gli è utile, semplicemente non deve essere versionato.

## Obiettivo

`pm/sources/` esiste localmente ma non viene mai committato/pushato.

## Acceptance Criteria

- [ ] `.gitignore` (root del repo) contiene una regola che esclude `pm/sources/` (suggerito: `pm/sources/`)
- [ ] `git status` non mostra come "untracked" nessun file dentro `pm/sources/`
- [ ] Decisione su `pm/sources/README.md`: il PM consiglia di **ignorarlo anch'esso** (è documentazione interna PM, non contributing guide del repo). Se Code/Ale preferiscono versionarlo come "spiegazione cartella per nuovi contributor", usare pattern tipo:
  ```
  pm/sources/*
  !pm/sources/README.md
  ```
  Decisione lasciata a Code/Ale, default = ignora tutto.

## File coinvolti

- `.gitignore` (root del repo)

## Vincoli / non-goals

- Non aggiungere altre regole di gitignore non richieste
- Non rimuovere file già versionati (la cartella non esisteva prima, no storico)
- Non spostare file esistenti

## Note

Il PM ha già creato dentro `pm/sources/`:
- `2026-05-04-call-paolo.md` — sintesi call con Paolo del 4 maggio
- `README.md` — convenzioni cartella

Quindi la cartella esiste e contiene 2 file. Aggiungere `.gitignore` PRIMA di un commit è importante: altrimenti `git add pm/` (che il PM in Cowork suggerisce all'utente) li trascinerebbe dentro al commit.

**Naming convention dei file futuri** (per memoria):
`YYYY-MM-DD-<tipo>-<topic>.md` — tipi: `call`, `mail`, `nota`, `doc`.

---

## 📤 Esito

**Esito:** ✅
**Cosa è stato fatto:**
- Aggiunta regola `pm/sources/` in `.gitignore` (root del repo), preceduta
  da commento `# PM private sources (call notes, mails, internal docs — never commit)`
- Scelta default applicata: ignora **tutto** dentro `pm/sources/` (incluso `README.md`),
  come consigliato dal PM. Se in futuro vuoi versionare `README.md` come spiegazione
  cartella, basta cambiare la regola in `pm/sources/*` + `!pm/sources/README.md`.

**File modificati:**
- `.gitignore`

**Commit:** vedi commit `chore(pm): gitignore pm/sources/ + archive handoff`

**Note per il PM:**
- ✅ `git status` ora non mostra più nulla dentro `pm/sources/` come untracked
- ✅ Quando il PM consiglia all'utente di chiedere `git add pm/`, io userò
  comunque path espliciti per i file PM (mai `git add pm/` cieco), ma con
  questa regola anche un add ricorsivo sarebbe safe.

**Follow-up emersi:**
- Nessuno.
