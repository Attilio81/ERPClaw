"""Agno Toolkit per la gestione logistica: ubicazioni, stock e movimenti di magazzino."""

from agno.tools import Toolkit
from erpclaw.erp_db import (
    get_session, init_db,
    Articolo, Ordine, RigaOrdine,
    Magazzino, Zona, Scaffale, Ripiano,
    StockUbicazione, MovimentoMagazzino, TipoMovimento,
    Indirizzo, Cliente,
)

init_db()


class LogisticaTools(Toolkit):
    def __init__(self):
        super().__init__(name="logistica_tools")
        self.register(self.crea_magazzino)
        self.register(self.crea_zona)
        self.register(self.crea_scaffale)
        self.register(self.crea_ripiano)
        self.register(self.lista_ubicazioni)
        self.register(self.assegna_stock)
        self.register(self.trasferisci_stock)
        self.register(self.stock_per_articolo)
        self.register(self.stock_per_ubicazione)
        self.register(self.articoli_senza_ubicazione)
        self.register(self.scarica_ordine_da_ubicazione)
        self.register(self.storico_movimenti)

    # ── ANAGRAFICA UBICAZIONI ─────────────────────────────────────────────────

    def crea_magazzino(self, codice: str, nome: str) -> str:
        """Crea un nuovo magazzino."""
        with get_session() as s:
            if s.query(Magazzino).filter_by(codice=codice).first():
                return f"Errore: esiste già un magazzino con codice {codice}."
            s.add(Magazzino(codice=codice, nome=nome))
            s.commit()
        return f"Magazzino **{codice} – {nome}** creato ✓"

    def crea_zona(self, codice: str, nome: str, codice_magazzino: str) -> str:
        """Crea una zona all'interno di un magazzino."""
        with get_session() as s:
            mag = s.query(Magazzino).filter_by(codice=codice_magazzino).first()
            if not mag:
                return f"Errore: magazzino {codice_magazzino} non trovato."
            if s.query(Zona).filter_by(codice=codice).first():
                return f"Errore: esiste già una zona con codice {codice}."
            s.add(Zona(codice=codice, nome=nome, magazzino_id=mag.id))
            s.commit()
        return f"Zona **{codice} – {nome}** creata in {codice_magazzino} ✓"

    def crea_scaffale(self, codice: str, nome: str, codice_zona: str) -> str:
        """Crea uno scaffale all'interno di una zona."""
        with get_session() as s:
            zona = s.query(Zona).filter_by(codice=codice_zona).first()
            if not zona:
                return f"Errore: zona {codice_zona} non trovata."
            if s.query(Scaffale).filter_by(codice=codice).first():
                return f"Errore: esiste già uno scaffale con codice {codice}."
            s.add(Scaffale(codice=codice, nome=nome, zona_id=zona.id))
            s.commit()
        return f"Scaffale **{codice} – {nome}** creato in zona {codice_zona} ✓"

    def crea_ripiano(self, codice: str, nome: str, codice_scaffale: str) -> str:
        """Crea un ripiano all'interno di uno scaffale."""
        with get_session() as s:
            scaffale = s.query(Scaffale).filter_by(codice=codice_scaffale).first()
            if not scaffale:
                return f"Errore: scaffale {codice_scaffale} non trovato."
            if s.query(Ripiano).filter_by(codice=codice).first():
                return f"Errore: esiste già un ripiano con codice {codice}."
            s.add(Ripiano(codice=codice, nome=nome, scaffale_id=scaffale.id))
            s.commit()
        return f"Ripiano **{codice} – {nome}** creato in scaffale {codice_scaffale} ✓"

    def lista_ubicazioni(self, codice_magazzino: str = None) -> str:
        """Mostra la gerarchia delle ubicazioni (magazzino → zona → scaffale → ripiano)."""
        with get_session() as s:
            query = s.query(Magazzino)
            if codice_magazzino:
                query = query.filter_by(codice=codice_magazzino)
            magazzini = query.order_by(Magazzino.codice).all()
            if not magazzini:
                return "Nessuna ubicazione configurata."
            lines = []
            for mag in magazzini:
                lines.append(f"**{mag.codice}** – {mag.nome}")
                for zona in sorted(mag.zone, key=lambda z: z.codice):
                    lines.append(f"  └ {zona.codice} – {zona.nome}")
                    for scaffale in sorted(zona.scaffali, key=lambda sc: sc.codice):
                        lines.append(f"    └ {scaffale.codice} – {scaffale.nome}")
                        for ripiano in sorted(scaffale.ripiani, key=lambda r: r.codice):
                            lines.append(f"      └ {ripiano.codice} – {ripiano.nome}")
        return "\n".join(lines)

    # ── GESTIONE STOCK ────────────────────────────────────────────────────────

    def assegna_stock(self, codice_articolo: str, codice_ripiano: str, quantita: int) -> str:
        """Assegna (o aggiunge) stock di un articolo a un ripiano. Genera un movimento di carico."""
        with get_session() as s:
            art = s.query(Articolo).filter_by(codice=codice_articolo).first()
            if not art:
                return f"Errore: articolo {codice_articolo} non trovato."
            ripiano = s.query(Ripiano).filter_by(codice=codice_ripiano).first()
            if not ripiano:
                return f"Errore: ripiano {codice_ripiano} non trovato."
            stock = s.query(StockUbicazione).filter_by(
                articolo_id=art.id, ripiano_id=ripiano.id
            ).first()
            if stock:
                stock.quantita += quantita
            else:
                stock = StockUbicazione(articolo_id=art.id, ripiano_id=ripiano.id, quantita=quantita)
                s.add(stock)
            s.add(MovimentoMagazzino(
                articolo_id=art.id,
                ripiano_destinazione_id=ripiano.id,
                quantita=quantita,
                tipo=TipoMovimento.carico,
            ))
            s.commit()
        return f"Stock **{codice_articolo}** in {codice_ripiano}: +{quantita} unità ✓"

    def trasferisci_stock(self, codice_articolo: str, codice_ripiano_origine: str,
                          codice_ripiano_dest: str, quantita: int) -> str:
        """Trasferisce stock di un articolo da un ripiano a un altro. Genera un movimento di trasferimento."""
        with get_session() as s:
            art = s.query(Articolo).filter_by(codice=codice_articolo).first()
            if not art:
                return f"Errore: articolo {codice_articolo} non trovato."
            r_orig = s.query(Ripiano).filter_by(codice=codice_ripiano_origine).first()
            r_dest = s.query(Ripiano).filter_by(codice=codice_ripiano_dest).first()
            if not r_orig:
                return f"Errore: ripiano origine {codice_ripiano_origine} non trovato."
            if not r_dest:
                return f"Errore: ripiano destinazione {codice_ripiano_dest} non trovato."
            stock_orig = s.query(StockUbicazione).filter_by(
                articolo_id=art.id, ripiano_id=r_orig.id
            ).first()
            if not stock_orig or stock_orig.quantita < quantita:
                disponibile = stock_orig.quantita if stock_orig else 0
                return f"Errore: stock insufficiente in {codice_ripiano_origine} (disponibile: {disponibile})."
            stock_orig.quantita -= quantita
            stock_dest = s.query(StockUbicazione).filter_by(
                articolo_id=art.id, ripiano_id=r_dest.id
            ).first()
            if stock_dest:
                stock_dest.quantita += quantita
            else:
                s.add(StockUbicazione(articolo_id=art.id, ripiano_id=r_dest.id, quantita=quantita))
            s.add(MovimentoMagazzino(
                articolo_id=art.id,
                ripiano_origine_id=r_orig.id,
                ripiano_destinazione_id=r_dest.id,
                quantita=quantita,
                tipo=TipoMovimento.trasferimento,
            ))
            s.commit()
        return f"Trasferiti {quantita}x **{codice_articolo}** da {codice_ripiano_origine} → {codice_ripiano_dest} ✓"

    def stock_per_articolo(self, codice_articolo: str) -> str:
        """Mostra la distribuzione dello stock di un articolo in tutte le ubicazioni."""
        with get_session() as s:
            art = s.query(Articolo).filter_by(codice=codice_articolo).first()
            if not art:
                return f"Errore: articolo {codice_articolo} non trovato."
            stocks = s.query(StockUbicazione).filter_by(articolo_id=art.id).all()
            if not stocks:
                return f"Nessuno stock ubicato per **{codice_articolo}**."
            rows = "\n".join(
                f"| {st.ripiano.codice} | {st.ripiano.scaffale.zona.magazzino.codice} | {st.quantita} |"
                for st in stocks
            )
        return f"**{codice_articolo}** – distribuzione stock:\n| Ripiano | Magazzino | Qtà |\n|---------|-----------|-----|\n{rows}"

    def stock_per_ubicazione(self, codice_ripiano: str) -> str:
        """Mostra tutti gli articoli presenti in un ripiano con le relative quantità."""
        with get_session() as s:
            ripiano = s.query(Ripiano).filter_by(codice=codice_ripiano).first()
            if not ripiano:
                return f"Errore: ripiano {codice_ripiano} non trovato."
            stocks = s.query(StockUbicazione).filter_by(ripiano_id=ripiano.id).all()
            if not stocks:
                return f"Nessun articolo nel ripiano **{codice_ripiano}**."
            rows = "\n".join(
                f"| {st.articolo.codice} | {st.articolo.descrizione} | {st.quantita} |"
                for st in stocks
            )
        return f"**{codice_ripiano}** – contenuto:\n| Codice | Descrizione | Qtà |\n|--------|-------------|-----|\n{rows}"

    def articoli_senza_ubicazione(self) -> str:
        """Elenca gli articoli con giacenza > 0 ma non presenti in nessuna ubicazione."""
        with get_session() as s:
            from sqlalchemy import not_, exists
            sub = exists().where(StockUbicazione.articolo_id == Articolo.id)
            articoli = s.query(Articolo).filter(
                not_(sub), Articolo.giacenza > 0
            ).all()
            if not articoli:
                return "Tutti gli articoli con giacenza > 0 hanno almeno un'ubicazione."
            rows = "\n".join(
                f"| {a.codice} | {a.descrizione} | {a.giacenza} |"
                for a in articoli
            )
        return f"**Articoli senza ubicazione:**\n| Codice | Descrizione | Giacenza |\n|--------|-------------|----------|\n{rows}"

    # ── INTEGRAZIONE ORDINI ───────────────────────────────────────────────────

    def scarica_ordine_da_ubicazione(self, numero_ordine: str) -> str:
        """Scarica le quantità di un ordine dalle ubicazioni (strategia LIFO: prima le ubicazioni con più stock).
        Fallisce se lo stock totale è insufficiente per qualsiasi articolo dell'ordine."""
        with get_session() as s:
            ordine = s.query(Ordine).filter_by(numero=numero_ordine).first()
            if not ordine:
                return f"Errore: ordine {numero_ordine} non trovato."
            righe = s.query(RigaOrdine).filter_by(ordine_id=ordine.id).all()
            if not righe:
                return f"Errore: l'ordine {numero_ordine} non ha righe."

            # Verifica preliminare disponibilità per tutti gli articoli
            for riga in righe:
                totale_stock = sum(
                    st.quantita for st in
                    s.query(StockUbicazione).filter_by(articolo_id=riga.articolo_id).all()
                )
                if totale_stock < riga.quantita:
                    return (
                        f"Errore: stock insufficiente per **{riga.articolo.codice}** "
                        f"(richiesto: {riga.quantita}, disponibile: {totale_stock})."
                    )

            # Esegui lo scarico
            log_lines = []
            for riga in righe:
                da_scaricare = riga.quantita
                stocks = (
                    s.query(StockUbicazione)
                    .filter_by(articolo_id=riga.articolo_id)
                    .order_by(StockUbicazione.quantita.desc())
                    .all()
                )
                for stock in stocks:
                    if da_scaricare <= 0:
                        break
                    prelevato = min(stock.quantita, da_scaricare)
                    stock.quantita -= prelevato
                    da_scaricare -= prelevato
                    s.add(MovimentoMagazzino(
                        articolo_id=riga.articolo_id,
                        ripiano_origine_id=stock.ripiano_id,
                        quantita=prelevato,
                        tipo=TipoMovimento.scarico,
                        ordine_id=ordine.id,
                    ))
                    log_lines.append(
                        f"  {riga.articolo.codice}: -{prelevato} da {stock.ripiano.codice}"
                    )
            s.commit()

            # Indirizzo spedizione cliente
            addr = next(
                (i for i in ordine.cliente.indirizzi if i.tipo.value == "spedizione"),
                next((i for i in ordine.cliente.indirizzi if i.tipo.value == "sede_legale"), None)
            )
            addr_str = ""
            if addr:
                addr_str = f"\n📦 Spedire a: {addr.via}, {addr.cap} {addr.citta} ({addr.provincia})"

        return (
            f"Scarico ordine **{numero_ordine}** completato ✓{addr_str}\n"
            + "\n".join(log_lines)
        )

    # ── STORICO ───────────────────────────────────────────────────────────────

    def storico_movimenti(self, codice_articolo: str = None, codice_ripiano: str = None,
                          limit: int = 20) -> str:
        """Mostra gli ultimi N movimenti di magazzino, filtrabili per articolo o ripiano."""
        with get_session() as s:
            q = s.query(MovimentoMagazzino)
            if codice_articolo:
                art = s.query(Articolo).filter_by(codice=codice_articolo).first()
                if not art:
                    return f"Errore: articolo {codice_articolo} non trovato."
                q = q.filter_by(articolo_id=art.id)
            if codice_ripiano:
                ripiano = s.query(Ripiano).filter_by(codice=codice_ripiano).first()
                if not ripiano:
                    return f"Errore: ripiano {codice_ripiano} non trovato."
                from sqlalchemy import or_
                q = q.filter(
                    or_(
                        MovimentoMagazzino.ripiano_origine_id == ripiano.id,
                        MovimentoMagazzino.ripiano_destinazione_id == ripiano.id,
                    )
                )
            movimenti = q.order_by(MovimentoMagazzino.data_ora.desc()).limit(limit).all()
            if not movimenti:
                return "Nessun movimento trovato."
            rows = "\n".join(
                f"| {m.data_ora.strftime('%Y-%m-%d %H:%M')} | {m.tipo.value} | {m.articolo.codice} | "
                f"{m.ripiano_origine.codice if m.ripiano_origine else '—'} → "
                f"{m.ripiano_destinazione.codice if m.ripiano_destinazione else '—'} | {m.quantita} |"
                for m in movimenti
            )
        return f"| Data | Tipo | Articolo | Ubicazione | Qtà |\n|------|------|----------|------------|-----|\n{rows}"
