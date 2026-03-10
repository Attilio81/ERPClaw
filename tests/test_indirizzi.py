# tests/test_indirizzi.py
from erpclaw.erp_db import Cliente, Fornitore, Indirizzo, TipoIndirizzo

def test_indirizzo_cliente(session):
    c = Cliente(codice="C001", ragione_sociale="Acme Srl")
    session.add(c)
    session.flush()
    addr = Indirizzo(
        tipo=TipoIndirizzo.spedizione,
        via="Via Roma 1", cap="20100", citta="Milano",
        provincia="MI", cliente_id=c.id
    )
    session.add(addr)
    session.commit()
    loaded = session.query(Indirizzo).filter_by(cliente_id=c.id).first()
    assert loaded.citta == "Milano"
    assert loaded.tipo == TipoIndirizzo.spedizione

def test_indirizzo_fornitore(session):
    f = Fornitore(codice="F001", ragione_sociale="Supplier Srl")
    session.add(f)
    session.flush()
    addr = Indirizzo(
        tipo=TipoIndirizzo.sede_legale,
        via="Via Po 5", cap="10100", citta="Torino",
        provincia="TO", fornitore_id=f.id
    )
    session.add(addr)
    session.commit()
    assert len(f.indirizzi) == 1
