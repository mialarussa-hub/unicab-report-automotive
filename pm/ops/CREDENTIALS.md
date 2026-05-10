# 🔐 CREDENTIALS — inventario

> **Qui dentro NON ci sono mai i secret.** Solo l'inventario di
> **dove** trovarli (file, secret manager, password manager, env del
> server, ecc.).

---

## Convenzione

| Servizio | Tipo credenziale | Dove si trova | Owner | Note |
|---|---|---|---|---|
| _esempio_ | API key | `.env` server prod (`/home/unicab/...`) | Ale | rotazione manuale |
| _esempio_ | DB password | 1Password / vault | Ale | — |

---

## Inventario

_(da compilare nel tempo, man mano che vengono integrati nuovi
servizi)_

| Servizio | Tipo credenziale | Dove si trova | Owner | Note |
|---|---|---|---|---|
| _—_ | _—_ | _—_ | _—_ | _—_ |

---

## Procedure

### Aggiungere una nuova credenziale
1. Salvare il segreto **fuori dal repo** (env server, secret manager, password manager).
2. Aggiungere una riga nella tabella sopra **descrivendo solo dove**.
3. Se è una env var: aggiornare `.env.example` con la chiave (senza valore).

### Rotazione
- Annotare data ultima rotazione nelle note.
- Per credenziali condivise, comunicare al team prima della rotazione.
