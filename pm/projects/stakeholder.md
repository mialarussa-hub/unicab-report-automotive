# 👥 Stakeholder UNICAB

Registro delle persone e delle entità coinvolte nel progetto UNICAB Report Automotive. Si aggiorna quando entrano/escono persone o cambiano ruoli.

**Ultimo aggiornamento:** 2026-05-11

---

## Lato Automica (esecuzione)

### Alessandro Pagani — "Ale"
- **Ruolo:** AI Specialist · founder Automica · lead developer · decisore tecnico
- **Email:** a.pagani@automica.it
- **Cell:** +39 338 133 7198
- **Indirizzo:** Viale Abbadia 16, 29121 Piacenza
- **Note:** unico operatore tecnico, gestisce tutto lo stack (scrapers, backend, frontend, infra). In rapporto contrattuale diretto con UNICAB Italia SRL.

### Fabrizio Capocasale
- **Ruolo:** **socio di Automica** di Ale, ha procurato il cliente UNICAB
- **Coinvolgimento:** presente al kickoff (6/3/2026), in CC iniziali. Da lato sales/relazione, non esecuzione tecnica.
- **Note:** **NON è lato cliente.** Confusione facile perché compare nelle prime comunicazioni con Paolo come "interlocutore" — in realtà è dalla parte di Ale.

---

## Lato cliente (UNICAB / Excellgo)

### Paolo Brunetti
- **Ruolo:** referente cliente principale, decisore prodotto
- **Email:** p.brunetti@excellgo.com (NB: dominio Excellgo, non UNICAB)
- **Coinvolgimento:** unico interlocutore operativo. Tutte le call e le mail passano da lui. Decide scope, fonti, priorità prodotto.
- **Sensibilità:** ha citato un evento familiare difficile (padre coinvolto nel progetto). Sui solleciti dare margine.
- **Modus operandi:** invia liste auto **a gruppetti**, non in un file unico.

### Pino Iacopino
- **Ruolo:** tecnico infrastruttura lato cliente, collega di Paolo
- **Email:** p.iacopino@excellgo.com
- **Coinvolgimento:** entrato nel progetto a inizio aprile 2026 (mail 2/4) per la parte infra. Call dedicata 8/4. Da allora non più attivo nei thread.
- **Note:** **non ha le credenziali del repo** (informazione utile per dimensionare il rischio leak su `Docs/Credentials.txt`).

### Fratello di Paolo
- **Ruolo:** decisore amministrativo/fatturazione lato cliente
- **Coinvolgimento:** **ininfluente operativamente** (parole di Ale). Paolo deve sentirlo per la questione fatturazione (a chi intestarla).
- **Note:** mai comparso direttamente nelle mail. Nome ignoto.

### `cnss2c@gmail.com` ("cns s2c")
- **Coinvolgimento:** in CC fino al 2 aprile 2026, poi sparisce dai thread.
- **Note:** identità non chiarita, **ininfluente** per il PM (parole di Ale 2026-05-11). Non tracciare oltre.

---

## Persone giuridiche

### UNICAB Italia S.r.l.
- **Indirizzo:** Via Livorno 20, 00162 Roma
- **Ruolo:** **cliente formale del contratto** (proposta progettuale 10/3/2026)
- **PI:** la proprietà intellettuale di tutto il lavoro (codice, workflow, template, asset) viene ceduta integralmente a UNICAB Italia SRL al saldo dell'importo
- **Account infrastruttura:** Hetzner Cloud (CX33 Norimberga) intestato a UNICAB Italia. Ale è "Member" del progetto, accesso revocabile.
- **Pubblicazione:** unicab.automica.it (dominio gestito da Automica per ora)

### Excellgo
- **Ruolo:** società di Paolo e Pino (entrambi @excellgo.com). Survey company (signature mostra `bi.surveys-excellgo.com`).
- **Coinvolgimento:** ipotetico soggetto di intestazione fatture (mail Paolo 23/4: "è molto probabile che le fatture e il contratto dovranno essere intestate ad un'altra società e non ad Unicab"). **Da confermare.**
- **Pending:** Paolo deve confermare con il fratello quale società sarà intestataria.

### Automica
- **Ruolo:** ditta individuale/professionista di Ale
- **Soci:** Ale + Fabrizio Capocasale
- **Sito:** www.automica.it
- **Regime fiscale:** forfettario (esente IVA L.190/2014 art.1 c.58). Fatture consuntive a fine mese.

---

## Domande aperte sugli stakeholder

- Excellgo vs UNICAB Italia per intestazione fatture: pending Paolo
- Il "fratello di Paolo" ha un nome / un ruolo formale in Excellgo o UNICAB?
- Esiste un secondo interlocutore lato cliente per coperture in assenza di Paolo? (al momento, no — single point of contact)

---

## Riferimenti

- Mail thread completi: `pm/sources/2026-*-mail-*.md`
- Briefing cliente: `pm/sources/2026-03-06-doc-presentazione-paolo.md`
- Proposta progettuale: `pm/sources/2026-03-10-doc-proposta-progettuale.md`
- Pivot driver comunicativi: `pm/sources/2026-04-23-mail-driver-comunicativi-fatturazione.md`
