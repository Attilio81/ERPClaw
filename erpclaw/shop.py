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

from erpclaw.config import SHOP_SECRET_KEY
from erpclaw.erp_db import Articolo, Cliente, ClienteAuth, Ordine, RigaOrdine, get_session

router = APIRouter(prefix="/shop")
templates = Jinja2Templates(directory="erpclaw/templates")
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
signer = URLSafeSerializer(SHOP_SECRET_KEY, salt="shop-session")

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
            confermato=True,
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
