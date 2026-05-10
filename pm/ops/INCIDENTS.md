# 🚨 INCIDENTS — log incidenti prod

> **Append-only, newest first.** Ogni incidente si aggiunge in cima.
> Non si cancella il passato.

---

## Formato

```
### YYYY-MM-DD HH:MM — [Titolo breve incidente]
- **Severità:** SEV1 (down) / SEV2 (degrado) / SEV3 (minore)
- **Durata:** dall'ora X all'ora Y
- **Sintomo:** cosa hanno visto gli utenti / il monitoring
- **Causa root:** cosa è effettivamente successo
- **Fix:** cosa è stato fatto per risolvere
- **Follow-up:** azioni preventive (link a SPRINT/BACKLOG se aperte)
```

---

## Log

_(vuoto — i nuovi incidenti vanno **in cima**, sopra questa riga)_
