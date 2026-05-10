# 🤝 HANDOFF — convenzioni PM → Code

Quando il PM AI ha bisogno che Claude Code esegua qualcosa, prepara un
**handoff**. Esistono due formati: inline (per task piccoli) e file
dedicato (per task complessi).

---

## Decisione: inline o file dedicato?

| Caso | Formato |
|---|---|
| Task da 1-2 step, contesto autoesplicativo | **Inline** in `pm/SPRINT.md`, colonna Note |
| Task con prerequisiti, criteri di accettazione, file multipli | **File dedicato** in `pm/pm-agent/handoff-YYYY-MM-DD-<x>-<topic>.md` |
| Bug fix di una riga | **Inline** |
| Nuova feature, refactor, integrazione esterna | **File dedicato** |
| Verifica ground truth (query DB, git log) | **Inline** se la richiesta è una sola, **file** se sono più verifiche |

In dubbio → file dedicato (meglio sovra-documentare).

---

## Format inline (in SPRINT.md)

Nella colonna **Note** della riga del task, scrivi qualcosa di
auto-contenuto:

```
[handoff Code] Verifica che la migration `0042_add_ai_comments` sia
applicata in prod (psql, conta colonne in tabella). Se manca,
applicarla. Riportare esito.
```

Convenzione: **prefisso `[handoff Code]`** così è subito riconoscibile.

---

## Format file dedicato

### Naming
```
pm/pm-agent/handoff-YYYY-MM-DD-<lettera>-<topic-breve>.md
```

- `YYYY-MM-DD` → data di creazione
- `<lettera>` → `a`, `b`, `c`... per disambiguare se ne crei più di uno
  nello stesso giorno
- `<topic-breve>` → 2-4 parole in kebab-case

Esempi:
- `handoff-2026-05-10-a-fix-login-bug.md`
- `handoff-2026-05-10-b-aggiungi-canale-youtube.md`
- `handoff-2026-05-12-a-deploy-minireport-v2.md`

### Riferimento in SPRINT
Nella riga del task in `SPRINT.md`, colonna Note:
```
→ pm/pm-agent/handoff-2026-05-10-a-fix-login-bug.md
```

### Struttura del file

Usa il template qui sotto.

---

## 📋 Template handoff

```markdown
# Handoff: [titolo task]

**Data:** YYYY-MM-DD
**Da:** PM AI
**A:** Claude Code
**Priorità:** P0 / P1 / P2
**Stima rough:** S (<1h) / M (1-4h) / L (>4h)
**Stato:** 🆕 Nuovo / 🔄 In corso / ✅ Completato / ❌ Bloccato

---

## Contesto

_Perché stiamo facendo questa cosa. 2-5 righe. Include il problema che
risolve e da dove viene la richiesta (utente, incident, sprint goal)._

## Obiettivo

_Cosa deve essere vero alla fine. Una frase, niente "come"._

## Acceptance Criteria

_Lista di condizioni verificabili che rendono il task "fatto"._

- [ ] Criterio 1
- [ ] Criterio 2
- [ ] _(es. "endpoint /api/x risponde 200 con body conforme a schema Y")_

## File coinvolti (sospetti)

_Lista di file o aree del codice probabilmente da toccare. Il PM non
conosce il codice nel dettaglio: questa lista è un'ipotesi, Code
verifica._

- `backend/...`
- `frontend/...`

## Vincoli / non-goals

_Cosa NON va fatto in questo handoff. Per evitare scope creep._

- Non rifattorizzare X
- Non toccare Y

## Note

_Qualsiasi info utile: link a discussioni, decisioni precedenti, ADR
correlati, output atteso da riportare al PM._

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
```

---

## 🗄️ Archiviazione

A handoff completato (esito riportato, task chiuso in SPRINT):

1. **Claude Code** sposta il file da `pm/pm-agent/` a
   `pm/pm-agent/handoff-archive/`
2. Aggiorna il riferimento in `SPRINT.md` (es. cambia il path al
   nuovo, oppure lascia risolto e basta — meglio cambiare path)
3. Append in `pm/DONE.md` come da routine standard

---

## ⚠️ Linee guida per scrivere buoni handoff

1. **Auto-contenuto.** Code legge l'handoff "a freddo": niente
   riferimenti a "come dicevamo prima".
2. **Cita file e path quando li sai.** Se non li sai, scrivi "il PM
   non sa dove sta esattamente, Code identifica".
3. **Acceptance criteria osservabili.** Niente "fai bene il login":
   "endpoint POST /login restituisce 200 con cookie sessione".
4. **Non prescrivere l'implementazione.** Decide Code (o l'utente).
   Tu descrivi il _cosa_, non il _come_.
5. **Non inventare dati.** Se non sai un valore (versione libreria,
   nome esatto endpoint), lascia placeholder e chiedi a Code di
   verificarlo.
