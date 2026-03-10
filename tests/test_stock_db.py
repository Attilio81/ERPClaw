# tests/test_stock_db.py
from erpclaw.erp_db import (
    Articolo, Magazzino, Zona, Scaffale, Ripiano,
    StockUbicazione, MovimentoMagazzino, TipoMovimento
)

def _setup_ubicazione(session):
    mag = Magazzino(codice="MAG1", nome="Principale")
    session.add(mag); session.flush()
    zona = Zona(codice="A", nome="Zona A", magazzino_id=mag.id)
    session.add(zona); session.flush()
    scaffale = Scaffale(codice="A-01", nome="Scaffale 1", zona_id=zona.id)
    session.add(scaffale); session.flush()
    ripiano = Ripiano(codice="A-01-1", nome="Ripiano 1", scaffale_id=scaffale.id)
    session.add(ripiano); session.flush()
    return ripiano

def test_stock_e_giacenza_derivata(session):
    art = Articolo(codice="ART001", descrizione="Widget", prezzo=9.99)
    session.add(art); session.flush()
    ripiano = _setup_ubicazione(session)

    stock = StockUbicazione(articolo_id=art.id, ripiano_id=ripiano.id, quantita=50)
    session.add(stock)
    session.commit()
    session.expire(art)

    assert art.giacenza == 50

def test_movimento_magazzino(session):
    art = Articolo(codice="ART002", descrizione="Gadget", prezzo=5.0)
    session.add(art); session.flush()
    ripiano = _setup_ubicazione(session)

    mov = MovimentoMagazzino(
        articolo_id=art.id,
        ripiano_destinazione_id=ripiano.id,
        quantita=10,
        tipo=TipoMovimento.carico,
    )
    session.add(mov)
    session.commit()
    assert mov.id is not None
