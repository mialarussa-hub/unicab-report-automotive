# Handoff: Scheda "Prestazioni & Piacere di guida" in L1 + verifica altre card driver

**Data:** 2026-05-12
**Da:** PM AI
**A:** Claude Code
**Priorità:** P1
**Stima rough:** M (1-4h)
**Stato:** 🆕 Nuovo

---

## Contesto

L1 oggi produce per ogni modello una serie di card-driver con
percentuale di "peso comunicativo" + citazioni dirette dal sito
brand (es. "Tecnologia & Innovazione 12%", "Sicurezza & ADAS 9%"
sulla Honda Jazz, con citazioni virgolettate sotto). In fondo alla
pagina compare una riga di testo **"Driver non comunicati:
Prestazioni & Piacere di guida, Heritage & Identità brand, Lifestyle
& Emozione..."** — quindi questi driver **esistono già nell'ontologia**
ma vengono mostrati come "non comunicati" relegati a una riga di
testo, non come card di pari dignità.

Paolo (in call 4/5 e re-confermato per la call 14/5 alle 15:30) ha
chiesto di **mettere a regime la scheda "Prestazioni"** in L1, dato
che è uno dei driver comunicativi più rilevanti per i modelli
sportivi/premium e per molti segmenti.

**Importante (framing):** L1 NON è "raccogli dati tecnici". L1 è
"leggi cosa il brand comunica del modello e classificalo per driver".
I numeri-chiave (0-100, potenza, peso, ecc.) servono come **evidenza
a corredo delle citazioni**, non come fine. Stessa logica delle card
esistenti (ADAS, Tecnologia): citazioni testuali dal sito brand +
attribuzione canale ("Canali: sito brand").

## Obiettivo

(1) La card **"Prestazioni & Piacere di guida"** è visibile in L1 con
la stessa estetica delle altre card-driver (percentuale + citazioni
+ canali), anche quando il brand non comunica quel driver (in tal
caso → card a 0% / "non comunicato" ma graficamente presente, non
relegata a una riga di testo in fondo).

(2) Quando il brand **sì** comunica le prestazioni, la card include
sotto le citazioni anche i **numeri-chiave prestazionali** del modello
presi dal sito ufficiale, come evidence di contesto.

(3) Stessa promozione "da riga di testo a card visibile" applicata
anche a **Heritage & Identità brand** e **Lifestyle & Emozione**
(verificare prima che siano effettivamente nell'ontologia driver e
non solo nella riga di testo).

## Acceptance Criteria

- [ ] La card "Prestazioni & Piacere di guida" è mostrata in L1 con
      lo stesso layout delle card driver attualmente comunicati
      (titolo, %, descrizione, citazioni virgolettate, "Canali: sito
      brand")
- [ ] Quando il driver è comunicato (es. modelli sportivi/premium) e
      ha % > 0, la card include in coda alle citazioni i **dati
      prestazionali estratti dal sito brand**: 0-100 km/h, velocità
      max, potenza (kW/CV), coppia, peso, rapporto peso/potenza,
      ripresa se disponibile. Per elettriche/ibride aggiungere
      autonomia WLTP e tempo di ricarica
- [ ] Quando il driver **non** è comunicato (% = 0), la card è
      comunque visibile con stato "non comunicato" — non più relegata
      alla riga di testo in fondo. Decidere se in quel caso mostrare
      comunque i numeri (utile per Paolo come benchmark) o lasciarla
      vuota: **proporre la scelta in FEEDBACK** prima di implementare
- [ ] Stesso trattamento applicato a **Heritage & Identità brand**
      e **Lifestyle & Emozione** (promozione a card visibile sempre)
- [ ] Verifica preliminare: queste 3 categorie sono effettivamente
      nell'ontologia driver oppure sono solo nomi in una stringa
      hard-coded? Se la seconda → segnalare in FEEDBACK come
      pre-requisito di disegno (allora va deciso con Ale)
- [ ] Test su **2 modelli pilota**: **Honda Jazz** (caso atteso: Honda
      non comunica prestazioni → card a 0% / "non comunicato") + **1
      premium o sportivo a scelta** (caso atteso: prestazioni
      comunicate → card valorizzata con citazioni + dati). Proporre
      il secondo modello in FEEDBACK se non ovvio da scelte
      precedenti
- [ ] Risultato accessibile in UI (sezione "Anteprima") al login Paolo

## File coinvolti (sospetti)

- Ontologia driver L1 (file da identificare — probabile in
  `scrapers/` o `backend/app/`)
- Pipeline analisi L1 sito brand (prompt AI che classifica le
  citazioni per driver — file da identificare)
- Template frontend che renderizza le card-driver (frontend/)
- Eventuale scraper dati tecnici (per i numeri prestazionali —
  potrebbe già esistere nel modulo "motore"/specs)

## Vincoli / non-goals

- **Non rifattorizzare** l'ontologia driver oltre la promozione delle
  3 categorie. Se si scopre che l'ontologia è messa male →
  segnalare in FEEDBACK come follow-up, non riscriverla qui
- **Non cambiare** il framing di L1 ("comunicazione brand", non
  "dati tecnici"). I numeri sono evidence sotto le citazioni, non
  l'oggetto principale della card
- **Non rifare** lo stile UI delle card esistenti — replicarlo
- Non aggiungere fonti diverse dal sito brand per questa card:
  l'attribuzione resta "Canali: sito brand"

## Note

- Esempio visivo del layout target: cfr. card "Tecnologia &
  Innovazione" e "Sicurezza & ADAS" già live su Honda Jazz. Stessa
  struttura per "Prestazioni" + le altre 2 promosse
- Se i dati prestazionali non sono tutti reperibili dal sito brand
  ufficiale (es. ripresa 80-120 spesso assente) → riportare solo
  quelli disponibili, non integrare da fonti terze in questo handoff
- Per il modello premium/sportivo del test, una scelta utile per
  Ale in call è qualcosa allineato col probabile prototipo (cfr.
  pending Paolo "numero modelli"): proporre 1-2 candidati e
  lasciare scegliere ad Ale in FEEDBACK se non ovvio

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
