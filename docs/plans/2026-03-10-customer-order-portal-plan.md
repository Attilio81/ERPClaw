# Customer Order Portal Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Portale web `/shop` integrato in FastAPI dove i clienti si registrano, cercano articoli con HTMX e inseriscono ordini.

**Architecture:** Nuove route FastAPI in `erpclaw/shop.py` montate su `web.py`. Template Jinja2 in `erpclaw/templates/shop/`. Autenticazione via cookie sessione firmati con `itsdangerous`, password hashate con `passlib[bcrypt]`. Carrello in cookie sessione JSON. HTMX per ricerca live articoli.

**Tech Stack:** FastAPI, Jinja2, HTMX (CDN), Bootstrap 5 (CDN), itsdangerous, passlib[bcrypt], SQLAlchemy (già presente)

---

### Task 1: Aggiungere dipendenze

**Files:**
- Modify: `pyproject.toml`

**Step 1: Aggiungere dipendenze al pyproject.toml**

Nel blocco `dependencies`, aggiungere dopo `"uvicorn>=0.34.0",`:
```toml
    "itsdangerous>=2.2.0",
    "passlib[bcrypt]>=1.7.4",
    "jinja2>=3.1.0",
    "python-multipart>=0.0.9",
```

`jinja2` è probabilmente già installata come dipendenza transitiva di FastAPI/sqladmin, ma dichiararla esplicitamente è corretto. `python-multipart` è richiesta da FastAPI per gestire i form HTML (POST con `Form(...)`).

**Step 2: Sincronizzare l'ambiente**

```bash
uv sync
```
Expected: no errors, pacchetti installati.

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add itsdangerous, passlib, jinja2, python-multipart for shop portal"
```

---

### Task 2: Aggiungere modello ClienteAuth al DB

**Files:**
- Modify: `erpclaw/erp_db.py`
- Test: `tests/test_shop_auth.py`

**Step 1: Scrivere il test failing**

Creare `tests/test_shop_auth.py`:

```python
"""Tests for ClienteAuth model."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from erpclaw.erp_db import Base, Cliente, ClienteAuth


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def test_cliente_auth_created_with_defaults(session):
    cliente = Cliente(codice="C001", ragione_sociale="Test Srl", email="test@example.com")
    session.add(cliente)
    session.flush()

    auth = ClienteAuth(cliente_id=cliente.id, password_hash="hashed")
    session.add(auth)
    session.commit()

    assert auth.id is not None
    assert auth.confermato is True
    assert auth.cliente.ragione_sociale == "Test Srl"
```

**Step 2: Eseguire il test per verificare che fallisca**

```bash
uv run pytest tests/test_shop_auth.py -v
```
Expected: FAIL con `ImportError: cannot import name 'ClienteAuth'`

**Step 3: Aggiungere il modello ClienteAuth in `erp_db.py`**

Aggiungere dopo la classe `Indirizzo` (dopo la riga `fornitore = relationship(...)`):

```python
class ClienteAuth(Base):
    __tablename__ = "clienti_auth"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clienti.id"), nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    confermato = Column(String, nullable=False, default="true")  # fittizio, sempre True

    cliente = relationship("Cliente", backref="auth")
```

Nota: `confermato` è stringa per compatibilità SQLite enum-less. In Python trattarlo come bool confrontando con `"true"`.

**Step 4: Eseguire il test**

```bash
uv run pytest tests/test_shop_auth.py -v
```
Expected: PASS

**Step 5: Verificare che i test esistenti non si rompano**

```bash
uv run pytest tests/ -v
```
Expected: tutti PASS

**Step 6: Commit**

```bash
git add erpclaw/erp_db.py tests/test_shop_auth.py
git commit -m "feat: add ClienteAuth model for shop portal authentication"
```

---

### Task 3: Creare i template Jinja2

**Files:**
- Create: `erpclaw/templates/shop/base.html`
- Create: `erpclaw/templates/shop/register.html`
- Create: `erpclaw/templates/shop/login.html`
- Create: `erpclaw/templates/shop/search.html`
- Create: `erpclaw/templates/shop/orders.html`

**Step 1: Creare la struttura directory**

```bash
mkdir -p erpclaw/templates/shop
```

**Step 2: Creare `erpclaw/templates/shop/base.html`**

```html
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ERPClaw Shop{% if title %} — {{ title }}{% endif %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://unpkg.com/htmx.org@2.0.3" defer></script>
</head>
<body>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
    <div class="container">
      <a class="navbar-brand" href="/shop/search">ERPClaw Shop</a>
      {% if cliente %}
      <div class="d-flex align-items-center gap-3">
        <a href="/shop/search" class="nav-link text-light">Cerca articoli</a>
        <a href="/shop/orders" class="nav-link text-light">I miei ordini</a>
        <span class="text-light small">{{ cliente.ragione_sociale }}</span>
        <a href="/shop/logout" class="btn btn-outline-light btn-sm">Esci</a>
      </div>
      {% endif %}
    </div>
  </nav>
  <div class="container">
    {% if error %}
    <div class="alert alert-danger">{{ error }}</div>
    {% endif %}
    {% if success %}
    <div class="alert alert-success">{{ success }}</div>
    {% endif %}
    {% block content %}{% endblock %}
  </div>
</body>
</html>
```

**Step 3: Creare `erpclaw/templates/shop/register.html`**

```html
{% extends "shop/base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-5">
    <h2 class="mb-4">Registrati</h2>
    <form method="post" action="/shop/register">
      <div class="mb-3">
        <label class="form-label">Ragione sociale</label>
        <input type="text" name="ragione_sociale" class="form-control" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Email</label>
        <input type="email" name="email" class="form-control" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Password</label>
        <input type="password" name="password" class="form-control" required minlength="6">
      </div>
      <button type="submit" class="btn btn-primary w-100">Registrati</button>
    </form>
    <p class="mt-3 text-center">Hai già un account? <a href="/shop/login">Accedi</a></p>
  </div>
</div>
{% endblock %}
```

**Step 4: Creare `erpclaw/templates/shop/login.html`**

```html
{% extends "shop/base.html" %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-5">
    <h2 class="mb-4">Accedi</h2>
    <form method="post" action="/shop/login">
      <div class="mb-3">
        <label class="form-label">Email</label>
        <input type="email" name="email" class="form-control" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Password</label>
        <input type="password" name="password" class="form-control" required>
      </div>
      <button type="submit" class="btn btn-primary w-100">Accedi</button>
    </form>
    <p class="mt-3 text-center">Non hai un account? <a href="/shop/register">Registrati</a></p>
  </div>
</div>
{% endblock %}
```

**Step 5: Creare `erpclaw/templates/shop/search.html`**

```html
{% extends "shop/base.html" %}
{% block content %}
<div class="row">
  <!-- Colonna ricerca articoli -->
  <div class="col-md-7">
    <h4>Cerca articoli</h4>
    <input
      type="search"
      name="q"
      class="form-control mb-3"
      placeholder="Cerca per codice o descrizione..."
      hx-get="/shop/search/results"
      hx-trigger="keyup changed delay:300ms, search"
      hx-target="#risultati"
      hx-swap="innerHTML"
      autofocus
    >
    <div id="risultati">
      <p class="text-muted">Inizia a digitare per cercare articoli.</p>
    </div>
  </div>
  <!-- Colonna carrello -->
  <div class="col-md-5">
    <h4>Carrello</h4>
    <div id="carrello">
      {% include "shop/_carrello.html" %}
    </div>
  </div>
</div>
{% endblock %}
```

**Step 6: Creare `erpclaw/templates/shop/_risultati.html`** (partial HTMX)

```html
{% if articoli %}
<table class="table table-sm table-hover">
  <thead><tr><th>Codice</th><th>Descrizione</th><th>Prezzo</th><th>Giacenza</th><th></th></tr></thead>
  <tbody>
    {% for a in articoli %}
    <tr>
      <td>{{ a.codice }}</td>
      <td>{{ a.descrizione }}</td>
      <td>€ {{ "%.2f"|format(a.prezzo) }}</td>
      <td>{{ a.giacenza }}</td>
      <td>
        <form method="post" action="/shop/cart/add"
              hx-post="/shop/cart/add"
              hx-target="#carrello"
              hx-swap="innerHTML">
          <input type="hidden" name="articolo_id" value="{{ a.id }}">
          <div class="input-group input-group-sm" style="width:110px">
            <input type="number" name="qty" value="1" min="1" max="{{ a.giacenza }}" class="form-control">
            <button class="btn btn-success btn-sm" type="submit">+</button>
          </div>
        </form>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% else %}
<p class="text-muted">Nessun articolo trovato.</p>
{% endif %}
```

**Step 7: Creare `erpclaw/templates/shop/_carrello.html`** (partial HTMX)

```html
{% if carrello %}
<table class="table table-sm">
  <thead><tr><th>Articolo</th><th>Qty</th><th>Prezzo</th><th></th></tr></thead>
  <tbody>
    {% for riga in carrello %}
    <tr>
      <td>{{ riga.codice }}<br><small class="text-muted">{{ riga.descrizione }}</small></td>
      <td>{{ riga.qty }}</td>
      <td>€ {{ "%.2f"|format(riga.prezzo * riga.qty) }}</td>
      <td>
        <form hx-post="/shop/cart/remove" hx-target="#carrello" hx-swap="innerHTML">
          <input type="hidden" name="articolo_id" value="{{ riga.articolo_id }}">
          <button class="btn btn-danger btn-sm">✕</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </tbody>
  <tfoot>
    <tr><td colspan="2"><strong>Totale</strong></td>
        <td colspan="2"><strong>€ {{ "%.2f"|format(totale) }}</strong></td></tr>
  </tfoot>
</table>
<form method="post" action="/shop/checkout">
  <button class="btn btn-primary w-100">Conferma ordine</button>
</form>
{% else %}
<p class="text-muted">Il carrello è vuoto.</p>
{% endif %}
```

**Step 8: Creare `erpclaw/templates/shop/orders.html`**

```html
{% extends "shop/base.html" %}
{% block content %}
<h4>I miei ordini</h4>
{% if ordini %}
<table class="table">
  <thead><tr><th>Numero</th><th>Data</th><th>Stato</th><th>Totale</th><th></th></tr></thead>
  <tbody>
    {% for o in ordini %}
    <tr>
      <td>{{ o.numero }}</td>
      <td>{{ o.data }}</td>
      <td><span class="badge bg-secondary">{{ o.stato }}</span></td>
      <td>€ {{ "%.2f"|format(o.totale) }}</td>
      <td>
        <button class="btn btn-sm btn-outline-secondary"
                data-bs-toggle="collapse"
                data-bs-target="#righe-{{ o.id }}">Dettaglio</button>
      </td>
    </tr>
    <tr class="collapse" id="righe-{{ o.id }}">
      <td colspan="5">
        <table class="table table-sm mb-0">
          {% for r in o.righe %}
          <tr>
            <td>{{ r.articolo.codice }}</td>
            <td>{{ r.articolo.descrizione }}</td>
            <td>{{ r.quantita }} pz</td>
            <td>€ {{ "%.2f"|format(r.prezzo_unitario) }}</td>
          </tr>
          {% endfor %}
        </table>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
{% else %}
<p class="text-muted">Nessun ordine ancora. <a href="/shop/search">Fai il tuo primo ordine!</a></p>
{% endif %}
{% endblock %}
```

**Step 9: Commit**

```bash
git add erpclaw/templates/
git commit -m "feat: add Jinja2 templates for shop portal"
```

---

### Task 4: Implementare shop.py — autenticazione

**Files:**
- Create: `erpclaw/shop.py`
- Test: `tests/test_shop_routes_auth.py`

**Step 1: Creare `erpclaw/shop.py` con autenticazione**

```python
"""Shop portal routes — customer-facing order entry."""

import json
import re
from datetime import date

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeSerializer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from erpclaw.erp_db import Articolo, Cliente, ClienteAuth, Ordine, RigaOrdine, get_session

router = APIRouter(prefix="/shop")
templates = Jinja2Templates(directory="erpclaw/templates")
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
signer = URLSafeSerializer("CAMBIA-QUESTA-CHIAVE-SEGRETA", salt="shop-session")

COOKIE_NAME = "shop_session"


def _set_session(response: Response, cliente_id: int) -> None:
    token = signer.dumps({"cliente_id": cliente_id})
    response.set_cookie(COOKIE_NAME, token, httponly=True, samesite="lax")


def _get_session_data(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        return signer.loads(token)
    except BadSignature:
        return None


def _get_cliente(request: Request) -> Cliente | None:
    data = _get_session_data(request)
    if not data:
        return None
    with get_session() as s:
        return s.get(Cliente, data["cliente_id"])


def _require_login(request: Request):
    """Returns (cliente, redirect_response). If redirect_response is not None, return it."""
    data = _get_session_data(request)
    if not data:
        return None, RedirectResponse("/shop/login", status_code=302)
    with get_session() as s:
        cliente = s.get(Cliente, data["cliente_id"])
    if not cliente:
        return None, RedirectResponse("/shop/login", status_code=302)
    return cliente, None


def _get_carrello(request: Request) -> list[dict]:
    raw = request.cookies.get("shop_cart", "[]")
    try:
        return json.loads(raw)
    except Exception:
        return []


def _set_carrello(response: Response, carrello: list[dict]) -> None:
    response.set_cookie("shop_cart", json.dumps(carrello), httponly=False, samesite="lax")


def _carrello_totale(carrello: list[dict]) -> float:
    return sum(r["prezzo"] * r["qty"] for r in carrello)


def _prossimo_numero_ordine(s: Session) -> str:
    today = date.today().strftime("%Y%m%d")
    prefix = f"WEB-{today}-"
    ultimo = (
        s.query(Ordine)
        .filter(Ordine.numero.like(f"{prefix}%"))
        .order_by(Ordine.numero.desc())
        .first()
    )
    if ultimo:
        n = int(ultimo.numero.split("-")[-1]) + 1
    else:
        n = 1
    return f"{prefix}{n:04d}"


# ── Registrazione ──────────────────────────────────────────────────────────────

@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("shop/register.html", {"request": request})


@router.post("/register")
def register(
    request: Request,
    ragione_sociale: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    with get_session() as s:
        if s.query(Cliente).filter_by(email=email).first():
            return templates.TemplateResponse(
                "shop/register.html",
                {"request": request, "error": "Email già registrata."},
            )
        # Codice auto: C-<sanitized email prefix>
        prefix = re.sub(r"[^a-zA-Z0-9]", "", email.split("@")[0])[:8].upper()
        base_code = f"WEB-{prefix}"
        code = base_code
        counter = 1
        while s.query(Cliente).filter_by(codice=code).first():
            code = f"{base_code}{counter}"
            counter += 1

        cliente = Cliente(codice=code, ragione_sociale=ragione_sociale, email=email)
        s.add(cliente)
        s.flush()
        auth = ClienteAuth(
            cliente_id=cliente.id,
            password_hash=pwd_ctx.hash(password),
            confermato="true",
        )
        s.add(auth)
        s.commit()

    return RedirectResponse("/shop/login?registered=1", status_code=302)


# ── Login / Logout ─────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    success = "Registrazione completata! Accedi ora." if request.query_params.get("registered") else None
    return templates.TemplateResponse("shop/login.html", {"request": request, "success": success})


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    with get_session() as s:
        cliente = s.query(Cliente).filter_by(email=email).first()
        if not cliente or not hasattr(cliente, "auth") or not cliente.auth:
            return templates.TemplateResponse(
                "shop/login.html",
                {"request": request, "error": "Credenziali non valide."},
            )
        auth = cliente.auth
        if not pwd_ctx.verify(password, auth.password_hash):
            return templates.TemplateResponse(
                "shop/login.html",
                {"request": request, "error": "Credenziali non valide."},
            )
        cliente_id = cliente.id

    response = RedirectResponse("/shop/search", status_code=302)
    _set_session(response, cliente_id)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/shop/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    response.delete_cookie("shop_cart")
    return response
```

**Step 2: Scrivere test per autenticazione**

Creare `tests/test_shop_routes_auth.py`:

```python
"""Tests for shop authentication helpers."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from erpclaw.erp_db import Base, Cliente, ClienteAuth
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def test_password_hash_verify(session):
    cliente = Cliente(codice="WEB-TEST", ragione_sociale="Test Srl", email="a@b.com")
    session.add(cliente)
    session.flush()
    hashed = pwd_ctx.hash("secret123")
    auth = ClienteAuth(cliente_id=cliente.id, password_hash=hashed, confermato="true")
    session.add(auth)
    session.commit()

    assert pwd_ctx.verify("secret123", auth.password_hash)
    assert not pwd_ctx.verify("wrong", auth.password_hash)


def test_prossimo_numero_ordine(session):
    from erpclaw.shop import _prossimo_numero_ordine
    n = _prossimo_numero_ordine(session)
    assert n.startswith("WEB-")
    parts = n.split("-")
    assert len(parts) == 3
    assert int(parts[2]) == 1
```

**Step 3: Eseguire i test**

```bash
uv run pytest tests/test_shop_routes_auth.py -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add erpclaw/shop.py tests/test_shop_routes_auth.py
git commit -m "feat: shop auth routes — register, login, logout"
```

---

### Task 5: Implementare shop.py — ricerca articoli e carrello

**Files:**
- Modify: `erpclaw/shop.py`
- Test: `tests/test_shop_cart.py`

**Step 1: Aggiungere le route di ricerca e carrello in `shop.py`**

Aggiungere alla fine di `erpclaw/shop.py`:

```python
# ── Ricerca articoli ───────────────────────────────────────────────────────────

@router.get("/search", response_class=HTMLResponse)
def search_page(request: Request):
    cliente, redir = _require_login(request)
    if redir:
        return redir
    carrello = _get_carrello(request)
    totale = _carrello_totale(carrello)
    return templates.TemplateResponse(
        "shop/search.html",
        {"request": request, "cliente": cliente, "carrello": carrello, "totale": totale},
    )


@router.get("/search/results", response_class=HTMLResponse)
def search_results(request: Request, q: str = ""):
    _, redir = _require_login(request)
    if redir:
        return redir
    articoli = []
    if q.strip():
        with get_session() as s:
            articoli = (
                s.query(Articolo)
                .filter(
                    (Articolo.codice.ilike(f"%{q}%"))
                    | (Articolo.descrizione.ilike(f"%{q}%"))
                )
                .limit(20)
                .all()
            )
            # Forza caricamento giacenza prima di chiudere la sessione
            articoli = [
                {"id": a.id, "codice": a.codice, "descrizione": a.descrizione,
                 "prezzo": a.prezzo, "giacenza": a.giacenza}
                for a in articoli
            ]
    return templates.TemplateResponse(
        "shop/_risultati.html",
        {"request": request, "articoli": articoli},
    )


# ── Carrello ───────────────────────────────────────────────────────────────────

@router.post("/cart/add", response_class=HTMLResponse)
def cart_add(request: Request, articolo_id: int = Form(...), qty: int = Form(...)):
    _, redir = _require_login(request)
    if redir:
        return redir
    carrello = _get_carrello(request)

    with get_session() as s:
        a = s.get(Articolo, articolo_id)
        if not a:
            return HTMLResponse("Articolo non trovato", status_code=404)
        codice, descrizione, prezzo = a.codice, a.descrizione, a.prezzo

    # Aggiorna qty se già presente, altrimenti aggiungi
    for riga in carrello:
        if riga["articolo_id"] == articolo_id:
            riga["qty"] += qty
            break
    else:
        carrello.append({
            "articolo_id": articolo_id,
            "codice": codice,
            "descrizione": descrizione,
            "prezzo": prezzo,
            "qty": qty,
        })

    totale = _carrello_totale(carrello)
    response = templates.TemplateResponse(
        "shop/_carrello.html",
        {"request": request, "carrello": carrello, "totale": totale},
    )
    _set_carrello(response, carrello)
    return response


@router.post("/cart/remove", response_class=HTMLResponse)
def cart_remove(request: Request, articolo_id: int = Form(...)):
    _, redir = _require_login(request)
    if redir:
        return redir
    carrello = [r for r in _get_carrello(request) if r["articolo_id"] != articolo_id]
    totale = _carrello_totale(carrello)
    response = templates.TemplateResponse(
        "shop/_carrello.html",
        {"request": request, "carrello": carrello, "totale": totale},
    )
    _set_carrello(response, carrello)
    return response
```

**Step 2: Scrivere test per le utility carrello**

Creare `tests/test_shop_cart.py`:

```python
"""Tests for shop cart utilities."""
from erpclaw.shop import _carrello_totale, _prossimo_numero_ordine
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from erpclaw.erp_db import Base, Cliente, Ordine
import pytest
from datetime import date


@pytest.fixture
def session():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


def test_carrello_totale_vuoto():
    assert _carrello_totale([]) == 0.0


def test_carrello_totale():
    carrello = [
        {"articolo_id": 1, "codice": "A1", "descrizione": "X", "prezzo": 10.0, "qty": 2},
        {"articolo_id": 2, "codice": "A2", "descrizione": "Y", "prezzo": 5.5, "qty": 1},
    ]
    assert _carrello_totale(carrello) == 25.5


def test_prossimo_numero_ordine_incrementa(session):
    cliente = Cliente(codice="C1", ragione_sociale="T", email="t@t.com")
    session.add(cliente)
    session.flush()
    today = date.today().strftime("%Y%m%d")
    ordine = Ordine(numero=f"WEB-{today}-0001", cliente_id=cliente.id, data=date.today())
    session.add(ordine)
    session.commit()

    n = _prossimo_numero_ordine(session)
    assert n == f"WEB-{today}-0002"
```

**Step 3: Eseguire i test**

```bash
uv run pytest tests/test_shop_cart.py -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add erpclaw/shop.py tests/test_shop_cart.py
git commit -m "feat: shop search and cart routes"
```

---

### Task 6: Implementare shop.py — checkout e storico ordini

**Files:**
- Modify: `erpclaw/shop.py`

**Step 1: Aggiungere checkout e orders in `shop.py`**

Aggiungere alla fine di `erpclaw/shop.py`:

```python
# ── Checkout ───────────────────────────────────────────────────────────────────

@router.post("/checkout")
def checkout(request: Request):
    cliente, redir = _require_login(request)
    if redir:
        return redir
    carrello = _get_carrello(request)
    if not carrello:
        return RedirectResponse("/shop/search", status_code=302)

    with get_session() as s:
        numero = _prossimo_numero_ordine(s)
        ordine = Ordine(numero=numero, cliente_id=cliente.id, data=date.today())
        s.add(ordine)
        s.flush()
        for riga in carrello:
            r = RigaOrdine(
                ordine_id=ordine.id,
                articolo_id=riga["articolo_id"],
                quantita=riga["qty"],
                prezzo_unitario=riga["prezzo"],
            )
            s.add(r)
        s.commit()

    response = RedirectResponse("/shop/orders?new=1", status_code=302)
    _set_carrello(response, [])
    return response


# ── Storico ordini ─────────────────────────────────────────────────────────────

@router.get("/orders", response_class=HTMLResponse)
def orders(request: Request):
    cliente, redir = _require_login(request)
    if redir:
        return redir

    with get_session() as s:
        raw_ordini = (
            s.query(Ordine)
            .filter_by(cliente_id=cliente.id)
            .order_by(Ordine.data.desc(), Ordine.numero.desc())
            .all()
        )
        # Materializza i dati prima di chiudere la sessione
        ordini_data = []
        for o in raw_ordini:
            righe = [
                {
                    "articolo": {"codice": r.articolo.codice, "descrizione": r.articolo.descrizione},
                    "quantita": r.quantita,
                    "prezzo_unitario": r.prezzo_unitario,
                }
                for r in o.righe
            ]
            ordini_data.append({
                "id": o.id,
                "numero": o.numero,
                "data": o.data,
                "stato": o.stato.value,
                "righe": righe,
                "totale": sum(r["quantita"] * r["prezzo_unitario"] for r in righe),
            })

    success = "Ordine inserito con successo!" if request.query_params.get("new") else None
    return templates.TemplateResponse(
        "shop/orders.html",
        {"request": request, "cliente": cliente, "ordini": ordini_data, "success": success},
    )
```

**Step 2: Aggiornare `orders.html` per usare dati dizionario**

Il template `orders.html` già creato nel Task 3 usa notazione punto — funziona anche con dizionari in Jinja2 (`o.numero` è equivalente a `o["numero"]` in Jinja2). Nessuna modifica necessaria.

**Step 3: Eseguire tutti i test**

```bash
uv run pytest tests/ -v
```
Expected: tutti PASS

**Step 4: Commit**

```bash
git add erpclaw/shop.py
git commit -m "feat: shop checkout and order history routes"
```

---

### Task 7: Registrare il router in web.py e configurare SECRET_KEY

**Files:**
- Modify: `erpclaw/web.py`
- Modify: `erpclaw/config.py`
- Modify: `erpclaw/shop.py`

**Step 1: Aggiungere `SHOP_SECRET_KEY` in `config.py`**

Leggere `erpclaw/config.py` e aggiungere la variabile (con default per sviluppo):

```python
import os
SHOP_SECRET_KEY = os.getenv("SHOP_SECRET_KEY", "dev-secret-change-in-production")
```

**Step 2: Usare `SHOP_SECRET_KEY` in `shop.py`**

In `shop.py`, sostituire:
```python
signer = URLSafeSerializer("CAMBIA-QUESTA-CHIAVE-SEGRETA", salt="shop-session")
```
con:
```python
from erpclaw.config import SHOP_SECRET_KEY
signer = URLSafeSerializer(SHOP_SECRET_KEY, salt="shop-session")
```

**Step 3: Registrare il router in `web.py`**

Aggiungere in `erpclaw/web.py` dopo `from fastapi import FastAPI`:
```python
from fastapi.staticfiles import StaticFiles
```

Aggiungere dopo `app = FastAPI(title="ERPClaw Admin")`:
```python
from erpclaw.shop import router as shop_router
app.include_router(shop_router)
```

**Step 4: Aggiungere `SHOP_SECRET_KEY` al `.env` di esempio**

Aggiungere nel file `.env` (se esiste):
```
SHOP_SECRET_KEY=cambia-questa-chiave-in-produzione
```

**Step 5: Avviare l'app e verificare manualmente**

```bash
uv run uvicorn erpclaw.web:app --reload
```

Aprire nel browser:
- `http://localhost:8000/shop/register` — deve mostrare form registrazione
- `http://localhost:8000/admin` — deve funzionare come prima

**Step 6: Commit**

```bash
git add erpclaw/web.py erpclaw/config.py erpclaw/shop.py .env
git commit -m "feat: register shop router in web app, use config secret key"
```

---

### Task 8: Test di integrazione end-to-end

**Files:**
- Test: `tests/test_shop_integration.py`

**Step 1: Scrivere test di integrazione**

Creare `tests/test_shop_integration.py`:

```python
"""Integration tests for shop portal using TestClient."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from erpclaw.erp_db import Base, Cliente, ClienteAuth, Articolo


@pytest.fixture(scope="module")
def test_engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture(scope="module")
def client(test_engine):
    def make_session():
        return Session(test_engine)

    with patch("erpclaw.shop.get_session", side_effect=make_session):
        from erpclaw.web import app
        with TestClient(app, follow_redirects=False) as c:
            yield c


@pytest.fixture(scope="module")
def seed_db(test_engine):
    with Session(test_engine) as s:
        art = Articolo(codice="ART001", descrizione="Prodotto Test", prezzo=9.99)
        s.add(art)
        s.commit()


def test_register_and_login(client, seed_db):
    # Registrazione
    r = client.post("/shop/register", data={
        "ragione_sociale": "Cliente Test Srl",
        "email": "cliente@test.com",
        "password": "password123",
    })
    assert r.status_code == 302
    assert "/shop/login" in r.headers["location"]

    # Login
    r = client.post("/shop/login", data={
        "email": "cliente@test.com",
        "password": "password123",
    })
    assert r.status_code == 302
    assert "/shop/search" in r.headers["location"]


def test_search_requires_login(client):
    # Senza cookie sessione → redirect login
    r = client.get("/shop/search")
    assert r.status_code == 302
```

**Step 2: Eseguire i test**

```bash
uv run pytest tests/test_shop_integration.py -v
```
Expected: PASS

**Step 3: Eseguire tutti i test**

```bash
uv run pytest tests/ -v
```
Expected: tutti PASS

**Step 4: Commit finale**

```bash
git add tests/test_shop_integration.py
git commit -m "test: add shop integration tests"
```

---

## Riepilogo file modificati/creati

| File | Azione |
|------|--------|
| `pyproject.toml` | Modify — nuove dipendenze |
| `erpclaw/erp_db.py` | Modify — aggiunta `ClienteAuth` |
| `erpclaw/config.py` | Modify — aggiunta `SHOP_SECRET_KEY` |
| `erpclaw/web.py` | Modify — registra `shop_router` |
| `erpclaw/shop.py` | Create — tutte le route `/shop` |
| `erpclaw/templates/shop/base.html` | Create |
| `erpclaw/templates/shop/register.html` | Create |
| `erpclaw/templates/shop/login.html` | Create |
| `erpclaw/templates/shop/search.html` | Create |
| `erpclaw/templates/shop/_risultati.html` | Create |
| `erpclaw/templates/shop/_carrello.html` | Create |
| `erpclaw/templates/shop/orders.html` | Create |
| `tests/test_shop_auth.py` | Create |
| `tests/test_shop_routes_auth.py` | Create |
| `tests/test_shop_cart.py` | Create |
| `tests/test_shop_integration.py` | Create |
