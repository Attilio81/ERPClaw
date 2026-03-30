"""CRM JSON API — GET/POST /crm/api/eventi, PUT/DELETE /crm/api/eventi/{id},
GET /crm/api/clienti/{id}/storico, POST /crm/api/clienti/{id}/note"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from erpclaw.erp_db import (
    get_session, EventoCRM, NotaCRM, Cliente,
    TipoEventoCRM, StatoEventoCRM,
)

router = APIRouter(prefix="/crm")


class _EventoCreate(BaseModel):
    cliente_id: Optional[int] = None
    tipo: str
    data_ora: str
    durata_minuti: Optional[int] = None
    luogo: Optional[str] = None
    note: Optional[str] = None


class _EventoUpdate(BaseModel):
    tipo: Optional[str] = None
    data_ora: Optional[str] = None
    durata_minuti: Optional[int] = None
    luogo: Optional[str] = None
    esito: Optional[str] = None
    note: Optional[str] = None
    stato: Optional[str] = None


class _NotaCreate(BaseModel):
    testo: str


def _ev_dict(ev: EventoCRM) -> dict:
    return {
        "id": ev.id,
        "tipo": ev.tipo.value,
        "stato": ev.stato.value,
        "data_ora": ev.data_ora.isoformat(),
        "durata_minuti": ev.durata_minuti,
        "luogo": ev.luogo,
        "esito": ev.esito,
        "note": ev.note,
        "cliente_id": ev.cliente_id,
        "cliente_nome": ev.cliente.ragione_sociale if ev.cliente else None,
        "reminder_inviato": ev.reminder_inviato,
    }


@router.get("/api/clienti")
async def list_clienti():
    """All clients — used by the React calendar for the client selector."""
    with get_session() as s:
        clienti = s.query(Cliente).order_by(Cliente.ragione_sociale).all()
        return JSONResponse([{"id": c.id, "ragione_sociale": c.ragione_sociale} for c in clienti])


@router.get("/api/eventi")
async def list_eventi(anno: int, mese: int):
    """Events for a given month — used by the React calendar feed."""
    d1 = datetime(anno, mese, 1)
    d2 = datetime(anno + 1, 1, 1) if mese == 12 else datetime(anno, mese + 1, 1)
    with get_session() as s:
        events = (
            s.query(EventoCRM)
            .filter(EventoCRM.data_ora >= d1, EventoCRM.data_ora < d2)
            .order_by(EventoCRM.data_ora)
            .all()
        )
        return JSONResponse([_ev_dict(ev) for ev in events])


@router.get("/api/eventi/{evento_id}")
async def get_evento(evento_id: int):
    with get_session() as s:
        ev = s.get(EventoCRM, evento_id)
        if not ev:
            raise HTTPException(404, "Evento non trovato")
        return JSONResponse(_ev_dict(ev))


@router.post("/api/eventi", status_code=201)
async def create_evento(body: _EventoCreate):
    try:
        tipo = TipoEventoCRM(body.tipo)
    except ValueError:
        raise HTTPException(422, f"tipo '{body.tipo}' non valido. Valori: visita, chiamata, email")
    try:
        dt = datetime.fromisoformat(body.data_ora)
    except ValueError:
        raise HTTPException(422, f"data_ora '{body.data_ora}' non valida")
    with get_session() as s:
        ev = EventoCRM(
            cliente_id=body.cliente_id,
            tipo=tipo,
            data_ora=dt,
            durata_minuti=body.durata_minuti,
            luogo=body.luogo,
            note=body.note,
            stato=StatoEventoCRM.pianificato,
            reminder_inviato=False,
        )
        s.add(ev)
        s.flush()
        data = _ev_dict(ev)
        s.commit()
        return JSONResponse(data, status_code=201)


@router.put("/api/eventi/{evento_id}")
async def update_evento(evento_id: int, body: _EventoUpdate):
    with get_session() as s:
        ev = s.get(EventoCRM, evento_id)
        if not ev:
            raise HTTPException(404, "Evento non trovato")
        if body.tipo is not None:
            try:
                ev.tipo = TipoEventoCRM(body.tipo)
            except ValueError:
                raise HTTPException(422, f"tipo '{body.tipo}' non valido")
        if body.data_ora is not None:
            try:
                ev.data_ora = datetime.fromisoformat(body.data_ora)
                ev.reminder_inviato = False
            except ValueError:
                raise HTTPException(422, f"data_ora '{body.data_ora}' non valida")
        if body.stato is not None:
            try:
                ev.stato = StatoEventoCRM(body.stato)
            except ValueError:
                raise HTTPException(422, f"stato '{body.stato}' non valido")
        if body.durata_minuti is not None:
            ev.durata_minuti = body.durata_minuti
        if body.luogo is not None:
            ev.luogo = body.luogo
        if body.esito is not None:
            ev.esito = body.esito
        if body.note is not None:
            ev.note = body.note
        s.flush()
        data = _ev_dict(ev)
        s.commit()
        return JSONResponse(data)


@router.delete("/api/eventi/{evento_id}")
async def delete_evento(evento_id: int):
    """Soft-delete: sets stato=annullato."""
    with get_session() as s:
        ev = s.get(EventoCRM, evento_id)
        if not ev:
            raise HTTPException(404, "Evento non trovato")
        ev.stato = StatoEventoCRM.annullato
        s.commit()
    return JSONResponse({"ok": True})


@router.get("/api/clienti/{cliente_id}/storico")
async def get_storico(cliente_id: int):
    with get_session() as s:
        c = s.get(Cliente, cliente_id)
        if not c:
            raise HTTPException(404, "Cliente non trovato")
        eventi = (
            s.query(EventoCRM)
            .filter_by(cliente_id=cliente_id)
            .order_by(EventoCRM.data_ora.desc())
            .all()
        )
        note = (
            s.query(NotaCRM)
            .filter_by(cliente_id=cliente_id)
            .order_by(NotaCRM.data_ora.desc())
            .all()
        )
        return JSONResponse({
            "eventi": [_ev_dict(ev) for ev in eventi],
            "note": [
                {
                    "id": n.id,
                    "cliente_id": n.cliente_id,
                    "testo": n.testo,
                    "data_ora": n.data_ora.isoformat(),
                    "autore": n.autore,
                }
                for n in note
            ],
        })


@router.post("/api/clienti/{cliente_id}/note", status_code=201)
async def add_nota(cliente_id: int, body: _NotaCreate):
    with get_session() as s:
        c = s.get(Cliente, cliente_id)
        if not c:
            raise HTTPException(404, "Cliente non trovato")
        nota = NotaCRM(
            cliente_id=cliente_id,
            testo=body.testo,
            data_ora=datetime.now(),
        )
        s.add(nota)
        s.commit()
        return JSONResponse({
            "id": nota.id,
            "cliente_id": nota.cliente_id,
            "testo": nota.testo,
            "data_ora": nota.data_ora.isoformat(),
            "autore": nota.autore,
        }, status_code=201)
