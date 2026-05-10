# 🚀 DEPLOY — runbook

Procedure di deploy e rollback per la piattaforma UNICAB.

---

## Ambiente

- **Server prod:** _da compilare_
- **URL pubblico:** _da compilare_
- **SSH:** _vedi `pm/ops/CREDENTIALS.md` per dove trovare la chiave_

---

## Deploy standard

### Pre-check
- [ ] Branch `main` aggiornato (`git pull`)
- [ ] Test/lint passano in locale (se applicabile)
- [ ] Migrazioni DB pronte (se applicabile)
- [ ] CHANGELOG / release note (se applicabile)

### Procedura
_(da compilare con i comandi reali — esempio sotto)_

```bash
# 1. SSH al server
# 2. cd nella dir del progetto
# 3. git pull
# 4. ricostruzione container / restart servizi
# 5. smoke test
```

### Post-deploy
- [ ] Verificare URL pubblico risponde
- [ ] Controllare log prime 5 minuti
- [ ] Annotare in `pm/DONE.md` (se era un task tracciato)

---

## Rollback

### Quando rollbackare
- Errori 5xx persistenti
- Funzione critica rotta (login, ingest, dashboard)
- Performance degradata > X%

### Procedura
_(da compilare)_

```bash
# 1. git revert / checkout commit precedente
# 2. rebuild + restart
# 3. verifica
```

---

## Note operative

_(quirks, gotchas, lezioni dal campo — appendere qui)_
