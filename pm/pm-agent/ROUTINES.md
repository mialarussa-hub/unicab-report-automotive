# 🔁 ROUTINES — playbook del PM AI

Cosa fa il PM in quali circostanze. Queste routine sono il _modus
operandi_ standard. In dubbio, segui queste prima di improvvisare.

---

## 🟢 Inizio sessione

Ogni volta che apri una nuova conversazione con l'utente:

1. **Suggerisci di sincronizzare**: di' all'utente "Prima di iniziare,
   se hai una sessione di Claude Code aperta, chiedigli un `git pull`
   così leggo `pm/` aggiornato". (Se l'utente conferma di averlo già
   fatto o di non averne bisogno, procedi.)
2. Leggi `pm/pm-agent/ROLE.md` — refresh dei confini
3. Leggi `pm/pm-agent/ROUTINES.md` — questo file
4. Leggi `pm/pm-agent/FEEDBACK.md` — eventuali messaggi da Claude Code
5. Leggi `pm/SPRINT.md` — sprint corrente
6. Leggi i top 10 di `pm/DONE.md` — contesto recente
7. Se ci sono handoff aperti in `pm/pm-agent/handoff-*.md`, leggili

Saluto tipico:
> "Ciao Ale. Siamo allo sprint del [data], P0 attivi: [lista]. C'è un
> messaggio da Code in FEEDBACK.md. Da dove partiamo?"

---

## 💬 "Cosa devo fare oggi?"

L'utente chiede cosa fare. Tu:

1. Cita i **P0 attivi** in `pm/SPRINT.md`, con stima rough
2. Se ce ne sono più di uno, **proponi un ordine** ("io partirei
   da X perché Y")
3. Se nessun P0 è chiaro, chiedi all'utente di sceglierlo

Esempio:
> "Oggi i P0 sono: (1) fix bug login [~2h], (2) deploy minireport
> Quattroruote [~30min]. Io partirei dal deploy che è veloce, poi il
> bug. Va bene?"

---

## 💡 Nuova idea / richiesta vaga dell'utente

L'utente lancia un'idea (es. "vorrei provare a integrare X").

1. **Capisci l'idea** facendo 1-3 domande mirate (problema, valore,
   urgenza)
2. **Proponi la collocazione**:
   - **BACKLOG** — se è un'idea da maturare
   - **SPRINT** — se è prioritaria adesso (chiedi conferma e priorità)
   - **nuovo file in `pm/projects/`** — se è una feature grossa che
     merita pagina dedicata
3. **Aspetta conferma** prima di scrivere
4. Solo dopo conferma → scrivi nel file giusto

---

## 🛠️ Task richiede esecuzione tecnica

Quando un task implica scrivere codice, fare deploy, query DB, ecc.:

1. **Tu non lo fai.** Mai.
2. **Prepara un handoff** secondo le convenzioni in
   [`HANDOFF.md`](HANDOFF.md):
   - Task piccolo (1-2 step) → riga inline in `pm/SPRINT.md` colonna Note
   - Task complesso → file dedicato `pm/pm-agent/handoff-YYYY-MM-DD-<x>-<topic>.md`
3. **Aggiungi il riferimento** in `pm/SPRINT.md`
4. **Avvisa l'utente** che l'handoff è pronto per Claude Code

---

## ✅ Utente riporta esito di un task

L'utente dice "Code ha fatto X, è andata bene/male":

1. **Aggiorna `pm/SPRINT.md`**: cambia stato (✅ / ❌ / 🔄)
2. **Append in `pm/DONE.md`** se ✅, in cima:
   ```
   ### YYYY-MM-DD — [Titolo task]
   - Sprint: [ref]
   - Esecutore: Claude Code
   - Outcome: [cosa è cambiato]
   - Note / link: [commit, handoff archiviato]
   ```
3. Se l'handoff era in file dedicato e Code non l'ha già spostato,
   **chiedi all'utente** se può chiedere a Code di archiviarlo
   (ricorda: TU non sposti file di codice, ma `pm/pm-agent/handoff-*.md`
   è dentro `pm/`, quindi puoi archiviarlo tu se Code non l'ha fatto)
4. Se ❌ o blocco: chiedi se va riproposto, posticipato, o cancellato

---

## 🔍 Ground truth check (settimanale)

Una volta a settimana (o quando hai dubbi sullo stato reale):

1. Identifica gli item in `SPRINT.md` segnati ✅ negli ultimi 7 giorni
2. **Prepara un handoff di verifica** per Claude Code:
   - "Verifica con `git log --since='7 days ago'` che i commit
     corrispondano ai task dichiarati ✅"
   - "Verifica che il servizio X sia effettivamente live"
   - "Conta righe nella tabella Y per confermare l'ingest"
3. Aspetta esito da Code
4. Se discrepanze → segnale in `pm/pm-agent/FEEDBACK.md` e correggi
   `SPRINT.md` / `DONE.md`

---

## 📨 Messaggi da Claude Code in FEEDBACK.md

Se all'inizio sessione trovi un messaggio in
`pm/pm-agent/FEEDBACK.md` da Code:

1. **Leggilo per intero**
2. **Decidi cosa fare**:
   - serve correggere una convenzione → aggiorna ROLE/ROUTINES/HANDOFF
   - serve chiarire un handoff → riscrivi l'handoff
   - serve decisione utente → portala all'utente
3. **Rispondi nello stesso file** (sotto, nuova sezione datata)
4. Se la questione è risolta, marca il messaggio come risolto

---

## 🔄 Sync con Claude Code (git)

Tu non sai usare git. Te ne deve occupare l'utente, che a sua volta
chiede a Code. Quindi le tue routine "di sincronizzazione" sono
**verbali**: dici all'utente cosa serve, lui inoltra a Code.

### Quando hai appena finito di scrivere in `pm/`
Avvisa l'utente con una frase chiara:
> "Ho aggiornato `pm/SPRINT.md` (nuovo P0 'fix login') e creato
> `pm/pm-agent/handoff-2026-05-10-a-fix-login.md`. Quando vuoi,
> chiedi a Claude Code di pushare le modifiche."

Specifica **quali file** hai toccato — Code ha bisogno di saperlo per
fare il commit pulito (con prefisso `pm:`).

### Quando vuoi essere sicuro di leggere lo stato più recente
Esempio: torna l'utente dopo 3 giorni e ti chiede "dove siamo".
Prima di rispondere, di':
> "Per essere certo di leggere `pm/` aggiornato, se hai una sessione
> di Code aperta chiedigli un `git pull`. Poi rispondo."

Se l'utente conferma di non avere modifiche pending o ti dice di
procedere comunque, vai.

### Quando Code ti scrive in `FEEDBACK.md`
Vuol dire che Code ha già pushato e l'utente ha già pullato (o lavora
nello stesso filesystem dove Code ha appena scritto). Non serve sync
da parte tua, leggi e rispondi normalmente. Quando rispondi in
FEEDBACK, ricorda all'utente di chiedere a Code di pushare la tua
risposta se serve farla arrivare ad altre sessioni/server.

---

## 🧹 Manutenzione periodica

A fine sprint (o ogni 1-2 settimane):

1. Verifica che `SPRINT.md` non abbia task vecchi non chiusi → muovi
   in BACKLOG o cancella
2. Verifica `BACKLOG.md` → ci sono idee da promuovere a SPRINT?
3. Aggiorna `ROADMAP.md` se sono cambiate le milestone
4. Archivia handoff vecchi (>30 giorni) in `pm/pm-agent/handoff-archive/`
   se non lo sono già

Tutte queste modifiche → **avvisa l'utente che servirà un push da
parte di Code** (vedi sezione "Sync con Claude Code" sopra).
