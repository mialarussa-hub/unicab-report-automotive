# 🚗 Release 0.0 — Prototipo "numero zero"

> Pagina di riferimento per la prima release prototipo di UNICAB.
> Distilla scope, vincoli, vision di prodotto, stakeholder e pending.
> Si aggiorna quando emergono decisioni nuove.

**Origine:** kickoff 26 marzo 2026 + call Paolo 4 maggio 2026.
**Stato:** in costruzione (Sprint 19-20, 11-24 maggio).
**Owner prodotto:** Paolo Brunetti (cliente).
**Owner tecnico:** Alessandro Pagani.

---

## Vision di prodotto

UNICAB Italia vuole un **prodotto editoriale mensile premium** per manager automotive. Lettura verticale e approfondita delle immatricolazioni italiane, dettaglio **fino alla singola versione del modello**, focus persone fisiche, gerarchia Italia→Regione→Provincia.

**Forma:** magazine data-driven stile **lab24/Sole 24 Ore** — *non* dashboard BI. Visualmente curato, narrativo, leggibile in 20-30 minuti.

**Tempestività:** pubblicazione **entro il 10 di ogni mese** (dati MTC rilasciati il 2-3 del mese). Processo molto automatizzato, intervento umano solo per validazione + normalizzazione DB mtc/quattroruote + scrittura/commenti alto livello.

**Scalabilità futura:** Germania, Spagna, poi moto/veicoli industriali/agricole/nautica. Piattaforma con abbonamenti, paywall, possibili pubblicazioni OEM riservate.

Fonti: `pm/sources/2026-03-06-doc-presentazione-paolo.md` (briefing Paolo).

---

## Cliente formale & contratto

**Cliente formale:** **UNICAB Italia S.r.l.** — Via Livorno 20, 00162 Roma.

**Proprietà intellettuale:** al saldo, **tutto è ceduto integralmente a UNICAB Italia SRL** (codice sorgente, workflow, architettura, template, asset). Ale non trattiene diritti. Eccezione: librerie e API di terze parti restano soggette ai propri T&C.

**Fatturazione contrattuale:** fatture consuntive a fine mese, regime forfettario (esente IVA L.190/2014 art.1 c.58).

⚠️ **Pending Paolo (mail 23/4 + call 4/5):** fattura potrebbe essere intestata a **società terza** (probabile Excellgo, da Paolo). Cambio rispetto al contratto originario. Paolo deve confermare con il fratello.

Fonti: `pm/sources/2026-03-10-doc-proposta-progettuale.md` (proposta progettuale).

---

## Filosofia della release

**"Numero zero"** = prototipo per pochi segmenti, non scala.
Approccio **modulare**: si scala solo dopo conferma di valore.
Costi tenuti sotto controllo, scraping ridotto al minimo necessario.

Target costi a regime: **~€100-150/mese** infra+API (dipendente dal numero di auto).

---

## Architettura — 4 layer

| Layer | Cosa fa | Stato per Release 0.0 |
|---|---|---|
| **L1** | Siti case automobilistiche + Perplexity Sonar Pro per web esteso | **De-prioritizzato.** Resta in produzione. Eccezione: aggiunta scheda "prestazioni" per segmenti C/D in su (test Honda Jazz). Vedi sotto "Driver comunicativi". |
| **L2** | **8 testate** scritte (AlVolante, Quattroruote, Motor1 Italia, Corriere Motori, Repubblica, La Stampa, Gazzetta, **Corriere dello Sport**) + **4 canali YouTube editoriali** (Quattroruote, AlVolante, Motor1 Italia, DriveK). Whisper su audio, top 30 commenti, minireport Claude Sonnet. | **Core.** Operativo. Da verificare se "solo YouTube" è sufficiente. |
| **L3** | Forum specializzati (Quattroruote XenForo, Autopareri IPS) + Reddit r/ItalyMotori via Arctic Shift + YouTube generico (DriveK, Quattroruote YT). Sentiment batch Claude Sonnet 4. | **In chiusura.** Stima residua ~8h+ a inizio sprint 19. |
| **L4** | Campagne advertising — bozza con MediaKey come fonte non-online suggerita da Paolo + Facebook Ads Library + Google Ads Transparency | **Da disegnare.** Esiste solo bozza. Avvio operativo sett. del 12 maggio. |

Manuali operativi dettagliati: `pm/sources/doc-flusso-l1.md`, `doc-flusso-l2.md`, `doc-flusso-l3.md`.

---

## Driver comunicativi — cronologia di un pivot

Tema importante che ha modificato il senso di L1 nel tempo:

| Data | Evento | Stato L1 |
|---|---|---|
| 2026-03-06 | Briefing Paolo: parla di "commenti editoriali ad alto valore" e "driver dei fenomeni", ma non distingue ancora L1 da dati tecnici | concetto implicito |
| 2026-04-09 | Prime Prove AI (allegato Paolo): L1 = "quali informazioni comunica la casa automobilistica" — già il seme dei driver comunicativi | implicito ma orientato a dati tecnici |
| 2026-04-22 | Ale → Paolo: descrive cosa L1 produce (trasmissione, consumi, emissioni, prezzi, allestimenti, dimensioni, potenza, dotazione, colori, ADAS). Chiede se è quello che vuole. | L1 scrape dati tecnici |
| 2026-04-23 | Paolo → Ale: **"non voglio dati tecnici, li ho già da listino Quattroruote. Voglio i driver comunicativi della casa automobilistica rispetto al modello: punta sulla linea? Sul prezzo? Su contenuti tecnologici? Sul risparmio consumi?"** | pivot esplicito |
| 2026-05-04 | Call Paolo: L1 de-prioritizzato del tutto per il prototipo. L2 (testate) cattura meglio i driver comunicativi (i giornalisti analizzano e riassumono i messaggi del brand). | L1 fuori scope |

**Implicazione operativa:** i "driver comunicativi" non hanno un flusso dedicato. Sono attualmente catturati come effetto laterale di L2 (testate riportano i messaggi delle case). Se in futuro Paolo li volesse esplicitamente, andrebbe disegnata una scheda L1 alternativa orientata al messaggio (non al dato tecnico).

---

## Scope IN (incluso nel prototipo)

- Scraping testate giornalistiche editoriali (cap 6 mesi temporale, max 15 pagine per ricerca)
- YouTube editoriale (download audio + Whisper + scraping commenti)
- Forum auto (Quattroruote, Autopareri, DriveK), Reddit
- Sentiment batch su commenti
- Adv (Facebook Ads Library + Google Ads) — quando L4 entra in funzione
- Schema modello con: brand, modello, versione, cilindrata, alimentazione, **prestazioni** (segmenti C/D in su)
- Tipi ibrido: Full (HEV), Mild (MHEV), Plug-in (PHEV), **Extended Range** (in arrivo, conferma Paolo)

## Scope OUT (rinviato — sta in `pm/BACKLOG.md`)

- Abbonamenti premium testate ("vediamo prima cosa raccogliamo gratis")
- Social testate (TikTok / IG / FB) — bloccato post-Cambridge Analytica
- Rubriche broadcaster motori (Mediaset / Sky / Rai) — tecnicamente complicato, basso ROI
- Riattivazione Perplexity Sonar (dipendenza API key cliente) — **NB: in realtà Perplexity Sonar Pro è già usato in L1 Strato B; nota in `00-stato-progetto.md` stale, da correggere via FEEDBACK**

---

## Vincoli operativi

- **Cap temporale:** 6 mesi sui contenuti L2-L4 (no articoli più vecchi)
- **Cap pagine:** max 15 pagine per ricerca
- **Scraping:** ridotto al minimo necessario per contenere costi
- **Lista auto:** Paolo invia **a gruppetti**, non in un file unico
- **Numero auto prototipo:** in attesa di decisione Paolo (ipotesi 500-1000 modello+versione, da ridurre a pochi segmenti per il prototipo)

---

## Decisioni prese (call 2026-05-04)

1. Niente abbonamenti premium testate in fase prototipo
2. Niente social testate in fase prototipo
3. Niente rubriche broadcaster in fase prototipo
4. L1 (siti case) de-prioritizzato per Release 0.0, focus su L2+L3+L4
5. Cap 6 mesi temporale sui contenuti
6. Cap 15 pagine per ricerca
7. Scraping ridotto al minimo

> _Quando saranno scritti gli ADR retroattivi (P2 sprint 19-20),
> queste decisioni andranno formalizzate in `pm/decisions/`._

---

## Stakeholder

Vedi `pm/projects/stakeholder.md` per dettaglio completo. Riassunto:

- **Paolo Brunetti** (`p.brunetti@excellgo.com`) — referente cliente, principale interlocutore.
- **Pino Iacopino** (`p.iacopino@excellgo.com`) — tecnico infrastruttura lato cliente.
- **Fratello di Paolo** — ininfluente operativamente, decide su fatturazione.
- **Fabrizio Capocasale** — socio Automica (lato Ale), ha procurato il cliente.
- **UNICAB Italia S.r.l.** — persona giuridica del contratto.
- **Excellgo** — società di Paolo e Pino, ipotesi di intestazione fatture (da chiarire).

---

## Timeline storica

| Data | Evento |
|---|---|
| 2026-03-02 | Invito Teams kickoff |
| 2026-03-06 | Call kickoff (Paolo + Fabrizio + Ale) + briefing UNICAB |
| 2026-03-10/11 | Proposta progettuale Ale (Release 0.0, 8 settimane, 25 giornate effort) |
| 2026-03-17 | Paolo conferma scope OK, normalizzazione DSET in corso |
| 2026-03-24 | Paolo finisce normalizzazione DSET |
| 2026-03-26 | Kickoff deck consegnato |
| 2026-03-27 | Proposta economica Ale (no infografiche) + Proposta Infrastrutturale (Hetzner vs OVHcloud) + stima costi AI |
| 2026-04-02 | Paolo formalizza fonti L1 (Quattroruote, Alvolante, Motor1, DriveK) + introduce Pino Iacopino |
| 2026-04-08 | Call con Pino su infrastruttura |
| 2026-04-09 | Follow-up Pino + allegato "Prime Prove AI" (liste modelli + struttura 4 livelli) |
| 2026-04-XX | Checklist Acquisto Hetzner (server CX33, Norimberga, SSH Ed25519, 3 opzioni deployment) |
| 2026-04-22 | Ale → Paolo: chiede precisazioni su scope L1 (dati tecnici) |
| 2026-04-23 | Paolo: pivot "driver comunicativi" + segnala fatturazione a società terza |
| 2026-04-29 | Ale completa L1+L2, sezione "Anteprima" live su unicab.automica.it |
| 2026-04-30 | Paolo dà feedback positivo, propone call 30/40' |
| 2026-05-04 | Call: de-prio L1, conferma cap 6 mesi, decisioni di scope, call successiva mer/gio 13-14 maggio |

---

## Pending Paolo

- [ ] Numero auto prototipo (entro prossima call)
- [ ] Conferma 4° tipo ibrido (Extended Range Hybrid — Nissan/BYD)
- [ ] Risposta su fatturazione mensile + soggetto fatturazione (UNICAB Italia o Excellgo)

## Pending Ale

- [ ] Chiusura L3 commenti (~8h+, vedi SPRINT)
- [ ] Test "solo YouTube" vs L2 completo
- [ ] Approfondimento bozza L4 (MediaKey, Facebook Ads Library, Google Ads)
- [ ] Aggiunta scheda "prestazioni" su L1 (Honda Jazz + segmenti C/D)

---

## Sensibilità

Paolo ha citato un **evento familiare difficile** ("è una cosa su cui stavo lavorando assieme a mio padre e mi fa un po' fatica di metterccela"). Sui solleciti, dare margine — non incalzare.

---

## Riferimenti

- **Mappa tecnica:** `CLAUDE.md` (root)
- **Stato tecnico:** `pm/projects/00-stato-progetto.md`
- **Sprint corrente:** `pm/SPRINT.md`
- **Stakeholder dettagliato:** `pm/projects/stakeholder.md`
- **Documenti fonte:** tutta `pm/sources/`
