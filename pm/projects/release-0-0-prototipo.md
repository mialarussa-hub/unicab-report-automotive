# 🚗 Release 0.0 — Prototipo "numero zero"

> Pagina di riferimento per la prima release prototipo di UNICAB.
> Distilla scope, vincoli e pending dalla call con Paolo del 2026-05-04.
> Si aggiorna quando emergono decisioni nuove.

**Origine:** call Paolo 2026-05-04 (~42 min, sintesi in `pm/sources/2026-05-04-call-paolo.md`).
**Stato:** in costruzione (Sprint 19-20, 11-24 maggio).
**Owner prodotto:** Paolo (cliente).
**Owner tecnico:** Ale.

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
| **L1** | Siti case automobilistiche | **De-prioritizzato.** Resta in produzione, ma non è core del prototipo. Eccezione: aggiunta scheda "prestazioni" per segmenti C/D in su (test su Honda Jazz). |
| **L2** | Testate giornalistiche + YouTube editoriale | **Core.** Operativo: 8 fonti news + 3 canali YouTube. Da verificare se YouTube da solo è sufficiente (test sprint corrente). |
| **L3** | Commenti utenti (forum, Reddit, YouTube comments, sentiment) | **In chiusura.** Stima residua ~8h+ a inizio sprint 19. |
| **L4** | Campagne advertising (Facebook Ads Library + Google Ads) | **Da disegnare.** Esiste solo una bozza. Avvio operativo settimana del 12 maggio. |

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
- Riattivazione Perplexity Sonar (dipendenza API key cliente)

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

## Pending Paolo

- [ ] Numero auto prototipo (entro prossima call)
- [ ] Conferma 4° tipo ibrido (Extended Range Hybrid — Nissan/BYD)
- [ ] Risposta su fatturazione mensile (consuntiva fine mese)

## Pending Ale

- [ ] Chiusura L3 commenti
- [ ] Test "solo YouTube" vs L2 completo
- [ ] Approfondimento bozza L4
- [ ] Aggiunta scheda "prestazioni" su L1 (Honda Jazz + segmenti C/D)

---

## Sensibilità

Paolo ha citato un **evento familiare difficile** ("è una cosa su cui stavo lavorando assieme a mio padre e mi fa un po' fatica di metterccela"). Sui solleciti, dare margine — non incalzare.

---

## Riferimenti

- Sintesi call: `pm/sources/2026-05-04-call-paolo.md` (locale, gitignored)
- Mappa tecnica: `CLAUDE.md` (root)
- Stato tecnico: `pm/projects/00-stato-progetto.md`
- Sprint corrente: `pm/SPRINT.md`
