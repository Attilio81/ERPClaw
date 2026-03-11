# Customer Order Portal — Design

**Date:** 2026-03-10
**Status:** Approved

## Overview

Portale web per clienti finali per inserire ordini senza usare Telegram.
Integrato nella stessa app FastAPI esistente, prefisso `/shop`.
Stack: Jinja2 + HTMX + Bootstrap 5 (CDN).

## Architettura

- Nuove route FastAPI in `erpclaw/shop.py`, registrate in `web.py`
- Template Jinja2 in `erpclaw/templates/shop/`
- Admin panel `/admin` invariato
- Autenticazione via cookie sessione firmati (`itsdangerous`)
- Password hashate con `passlib[bcrypt]`

## Nuovo modello DB: `ClienteAuth`

Tabella `clienti_auth`:

| Campo | Tipo | Note |
|-------|------|------|
| id | Integer PK | |
| cliente_id | FK → clienti.id | unique |
| password_hash | String | bcrypt |
| confermato | Boolean | default=True (fittizio) |

## Flusso registrazione

1. GET `/shop/register` → form (ragione_sociale, email, password)
2. POST `/shop/register` → crea `Cliente` + `ClienteAuth(confermato=True)`
3. Redirect a `/shop/login`

## Flusso ordine

1. Login → sessione cookie con `cliente_id`
2. `/shop/search` → campo ricerca, HTMX chiama `/shop/search/results?q=...`
3. Aggiunta al carrello → POST `/shop/cart/add` (carrello in cookie sessione JSON)
4. Checkout → POST `/shop/checkout` → crea `Ordine(stato=bozza)` + `RigaOrdine` per ogni riga
5. Redirect a `/shop/orders`

## Carrello (cookie sessione)

```json
{"carrello": [{"articolo_id": 1, "codice": "ART001", "descrizione": "...", "prezzo": 10.0, "qty": 2}]}
```

## Numero ordine automatico

Formato: `WEB-YYYYMMDD-NNNN` (es. `WEB-20260310-0001`)

## Route HTTP

| Metodo | Path | Descrizione |
|--------|------|-------------|
| GET | `/shop/register` | Form registrazione |
| POST | `/shop/register` | Crea Cliente + ClienteAuth |
| GET | `/shop/login` | Form login |
| POST | `/shop/login` | Setta cookie sessione |
| GET | `/shop/logout` | Cancella sessione |
| GET | `/shop/search` | Pagina ricerca + carrello |
| GET | `/shop/search/results` | HTMX partial — risultati ricerca |
| POST | `/shop/cart/add` | Aggiunge al carrello |
| POST | `/shop/cart/remove` | Rimuove dal carrello |
| GET | `/shop/cart` | HTMX partial — carrello aggiornato |
| POST | `/shop/checkout` | Conferma ordine |
| GET | `/shop/orders` | Storico ordini cliente |

## Nuovi file

```
erpclaw/
  shop.py
  templates/
    shop/
      base.html
      register.html
      login.html
      search.html
      orders.html
```

## Dipendenze aggiuntive

- `itsdangerous` — firma cookie sessione
- `passlib[bcrypt]` — hash password

## Fuori scope

- Email reale di conferma registrazione
- Pagamento
- Gestione indirizzi di spedizione nel portale
