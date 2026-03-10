# tests/test_ubicazioni_db.py
from erpclaw.erp_db import Magazzino, Zona, Scaffale, Ripiano

def test_gerarchia_ubicazioni(session):
    mag = Magazzino(codice="MAG1", nome="Magazzino Principale")
    session.add(mag)
    session.flush()

    zona = Zona(codice="A", nome="Zona A", magazzino_id=mag.id)
    session.add(zona)
    session.flush()

    scaffale = Scaffale(codice="A-03", nome="Scaffale 3", zona_id=zona.id)
    session.add(scaffale)
    session.flush()

    ripiano = Ripiano(codice="A-03-2", nome="Ripiano 2", scaffale_id=scaffale.id)
    session.add(ripiano)
    session.commit()

    assert ripiano.scaffale.zona.magazzino.codice == "MAG1"
