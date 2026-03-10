"""Agno Toolkit with all ERP tools for articles, customers and orders."""

from agno.tools import Toolkit
from sqlalchemy import or_, func

from erpclaw.erp_db import (
    get_session, init_db,
    Articolo, Cliente, Ordine, RigaOrdine, StatoOrdine,
    Fornitore, CatalogoFornitore,
    Indirizzo, TipoIndirizzo,
    Categoria,
    OrdineFornitore, RigaOrdineFornitore, StatoOrdineFornitore,
)

init_db()


class ERPTools(Toolkit):
    def __init__(self):
        super().__init__(name="erp_tools")
        self.register(self.crea_articolo)
        self.register(self.lista_articoli)
        self.register(self.cerca_articolo)
        self.register(self.aggiorna_articolo)
        self.register(self.crea_cliente)
        self.register(self.lista_clienti)
        self.register(self.cerca_cliente)
        self.register(self.aggiorna_cliente)
        self.register(self.crea_ordine)
        self.register(self.aggiungi_riga)
        self.register(self.rimuovi_riga)
        self.register(self.dettaglio_ordine)
        self.register(self.lista_ordini)
        self.register(self.aggiorna_stato_ordine)
        self.register(self.vendite_per_cliente)
        self.register(self.articoli_sotto_soglia)
        self.register(self.crea_fornitore)
        self.register(self.lista_fornitori)
        self.register(self.cerca_fornitore)
        self.register(self.aggiorna_fornitore)
        self.register(self.lista_cataloghi_fornitore)
        self.register(self.aggiungi_indirizzo_cliente)
        self.register(self.aggiungi_indirizzo_fornitore)
        self.register(self.lista_indirizzi_cliente)
        self.register(self.lista_indirizzi_fornitore)
        self.register(self.crea_categoria)
        self.register(self.lista_categorie)
        self.register(self.assegna_categoria)
        self.register(self.articoli_sotto_scorta_minima)

    # ── ARTICOLI ──────────────────────────────────────────────────────────────

    def crea_articolo(self, codice: str, descrizione: str, prezzo_vendita: float, prezzo_acquisto: float = None) -> str:
        """Crea un nuovo articolo nel catalogo con prezzo di vendita e (opzionale) prezzo di acquisto."""
        with get_session() as s:
            if s.query(Articolo).filter_by(codice=codice).first():
                return f"Errore: esiste già un articolo con codice {codice}."
            s.add(Articolo(codice=codice, descrizione=descrizione,
                           prezzo_vendita=prezzo_vendita, prezzo_acquisto=prezzo_acquisto))
            s.commit()
        return f"Articolo **{codice}** creato ✓"

    def lista_articoli(self) -> str:
        """Restituisce la lista di tutti gli articoli."""
        with get_session() as s:
            articoli = s.query(Articolo).order_by(Articolo.codice).all()
            if not articoli:
                return "Nessun articolo presente."
            rows = "\n".join(
                f"| {a.codice} | {a.descrizione} | {a.categoria.nome if a.categoria else '—'} | €{a.prezzo_vendita:.2f} | {f'€{a.prezzo_acquisto:.2f}' if a.prezzo_acquisto else '—'} | {a.giacenza} |"
                for a in articoli
            )
        return f"| Codice | Descrizione | Categoria | Prezzo Vendita | Prezzo Acquisto | Giacenza |\n|--------|-------------|-----------|----------------|-----------------|----------|\n{rows}"

    def cerca_articolo(self, testo: str) -> str:
        """Cerca articoli per codice o descrizione (ricerca parziale)."""
        with get_session() as s:
            like = f"%{testo}%"
            articoli = s.query(Articolo).filter(
                or_(Articolo.codice.ilike(like), Articolo.descrizione.ilike(like))
            ).all()
            if not articoli:
                return f"Nessun articolo trovato per '{testo}'."
            rows = "\n".join(
                f"| {a.codice} | {a.descrizione} | {a.categoria.nome if a.categoria else '—'} | €{a.prezzo_vendita:.2f} | {f'€{a.prezzo_acquisto:.2f}' if a.prezzo_acquisto else '—'} | {a.giacenza} |"
                for a in articoli
            )
        return f"| Codice | Descrizione | Categoria | Prezzo Vendita | Prezzo Acquisto | Giacenza |\n|--------|-------------|-----------|----------------|-----------------|----------|\n{rows}"

    def aggiorna_articolo(self, codice: str, descrizione: str = None,
                          prezzo_vendita: float = None, prezzo_acquisto: float = None) -> str:
        """Aggiorna descrizione, prezzo di vendita o prezzo di acquisto di un articolo esistente."""
        with get_session() as s:
            a = s.query(Articolo).filter_by(codice=codice).first()
            if not a:
                return f"Errore: articolo {codice} non trovato."
            if descrizione is not None:
                a.descrizione = descrizione
            if prezzo_vendita is not None:
                a.prezzo_vendita = prezzo_vendita
            if prezzo_acquisto is not None:
                a.prezzo_acquisto = prezzo_acquisto
            s.commit()
        return f"Articolo **{codice}** aggiornato ✓"

    # ── CLIENTI ───────────────────────────────────────────────────────────────

    def crea_cliente(self, codice: str, ragione_sociale: str, email: str = "", telefono: str = "") -> str:
        """Crea un nuovo cliente."""
        with get_session() as s:
            if s.query(Cliente).filter_by(codice=codice).first():
                return f"Errore: esiste già un cliente con codice {codice}."
            s.add(Cliente(codice=codice, ragione_sociale=ragione_sociale, email=email, telefono=telefono))
            s.commit()
        return f"Cliente **{codice} – {ragione_sociale}** creato ✓"

    def lista_clienti(self) -> str:
        """Restituisce la lista di tutti i clienti."""
        with get_session() as s:
            clienti = s.query(Cliente).order_by(Cliente.codice).all()
            if not clienti:
                return "Nessun cliente presente."
            rows = "\n".join(
                f"| {c.codice} | {c.ragione_sociale} | {c.email} | {c.telefono} |"
                for c in clienti
            )
        return f"| Codice | Ragione Sociale | Email | Telefono |\n|--------|-----------------|-------|----------|\n{rows}"

    def cerca_cliente(self, testo: str) -> str:
        """Cerca clienti per codice o ragione sociale (ricerca parziale)."""
        with get_session() as s:
            like = f"%{testo}%"
            clienti = s.query(Cliente).filter(
                or_(Cliente.codice.ilike(like), Cliente.ragione_sociale.ilike(like))
            ).all()
            if not clienti:
                return f"Nessun cliente trovato per '{testo}'."
            rows = "\n".join(
                f"| {c.codice} | {c.ragione_sociale} | {c.email} | {c.telefono} |"
                for c in clienti
            )
        return f"| Codice | Ragione Sociale | Email | Telefono |\n|--------|-----------------|-------|----------|\n{rows}"

    def aggiungi_indirizzo_cliente(self, codice_cliente: str, tipo: str, via: str,
                                   cap: str, citta: str, provincia: str,
                                   paese: str = "IT", note: str = "") -> str:
        """Aggiunge un indirizzo (sede_legale/spedizione/fatturazione/altro) a un cliente."""
        with get_session() as s:
            c = s.query(Cliente).filter_by(codice=codice_cliente).first()
            if not c:
                return f"Errore: cliente {codice_cliente} non trovato."
            try:
                t = TipoIndirizzo(tipo)
            except ValueError:
                return f"Errore: tipo '{tipo}' non valido. Valori: sede_legale, spedizione, fatturazione, altro."
            s.add(Indirizzo(tipo=t, via=via, cap=cap, citta=citta,
                            provincia=provincia, paese=paese, note=note, cliente_id=c.id))
            s.commit()
        return f"Indirizzo **{tipo}** aggiunto al cliente {codice_cliente} ✓"

    def lista_indirizzi_cliente(self, codice_cliente: str) -> str:
        """Mostra tutti gli indirizzi di un cliente."""
        with get_session() as s:
            c = s.query(Cliente).filter_by(codice=codice_cliente).first()
            if not c:
                return f"Errore: cliente {codice_cliente} non trovato."
            if not c.indirizzi:
                return f"Nessun indirizzo per il cliente {codice_cliente}."
            rows = "\n".join(
                f"| {i.tipo.value} | {i.via} | {i.cap} {i.citta} ({i.provincia}) | {i.paese} |"
                for i in c.indirizzi
            )
        return f"| Tipo | Via | Città | Paese |\n|------|-----|-------|-------|\n{rows}"

    def aggiorna_cliente(self, codice: str, ragione_sociale: str = None, email: str = None, telefono: str = None) -> str:
        """Aggiorna i dati di un cliente esistente."""
        with get_session() as s:
            c = s.query(Cliente).filter_by(codice=codice).first()
            if not c:
                return f"Errore: cliente {codice} non trovato."
            if ragione_sociale is not None:
                c.ragione_sociale = ragione_sociale
            if email is not None:
                c.email = email
            if telefono is not None:
                c.telefono = telefono
            s.commit()
        return f"Cliente **{codice}** aggiornato ✓"

    # ── ORDINI ────────────────────────────────────────────────────────────────

    def crea_ordine(self, codice_cliente: str) -> str:
        """Crea un nuovo ordine in stato bozza per il cliente indicato."""
        with get_session() as s:
            cliente = s.query(Cliente).filter_by(codice=codice_cliente).first()
            if not cliente:
                return f"Errore: cliente {codice_cliente} non trovato."
            count = s.query(Ordine).count()
            numero = f"ORD-{count + 1:04d}"
            from datetime import date
            ordine = Ordine(numero=numero, data=date.today(), cliente_id=cliente.id)
            s.add(ordine)
            s.commit()
            return f"Ordine **{numero}** creato per {cliente.ragione_sociale} (stato: bozza) ✓\nAggiungi le righe con `aggiungi_riga`."

    def aggiungi_riga(self, numero_ordine: str, codice_articolo: str, quantita: int) -> str:
        """Aggiunge una riga a un ordine esistente."""
        with get_session() as s:
            ordine = s.query(Ordine).filter_by(numero=numero_ordine).first()
            if not ordine:
                return f"Errore: ordine {numero_ordine} non trovato."
            articolo = s.query(Articolo).filter_by(codice=codice_articolo).first()
            if not articolo:
                return f"Errore: articolo {codice_articolo} non trovato."
            # controlla se riga già presente → aggiorna quantità
            riga = s.query(RigaOrdine).filter_by(ordine_id=ordine.id, articolo_id=articolo.id).first()
            if riga:
                riga.quantita += quantita
            else:
                riga = RigaOrdine(
                    ordine_id=ordine.id,
                    articolo_id=articolo.id,
                    quantita=quantita,
                    prezzo_unitario=articolo.prezzo_vendita,
                )
                s.add(riga)
            s.commit()
            # ricalcola totale
            righe = s.query(RigaOrdine).filter_by(ordine_id=ordine.id).all()
            totale = sum(r.quantita * r.prezzo_unitario for r in righe)
            articolo_desc = articolo.descrizione
            articolo_prezzo = articolo.prezzo_vendita
            subtotale = quantita * articolo_prezzo
        return (
            f"Riga aggiunta: {quantita}x **{articolo_desc}** @ €{articolo_prezzo:.2f} = €{subtotale:.2f}\n"
            f"Totale ordine **{numero_ordine}**: €{totale:.2f}"
        )

    def rimuovi_riga(self, numero_ordine: str, codice_articolo: str) -> str:
        """Rimuove una riga da un ordine."""
        with get_session() as s:
            ordine = s.query(Ordine).filter_by(numero=numero_ordine).first()
            if not ordine:
                return f"Errore: ordine {numero_ordine} non trovato."
            articolo = s.query(Articolo).filter_by(codice=codice_articolo).first()
            if not articolo:
                return f"Errore: articolo {codice_articolo} non trovato."
            riga = s.query(RigaOrdine).filter_by(ordine_id=ordine.id, articolo_id=articolo.id).first()
            if not riga:
                return f"Errore: riga con articolo {codice_articolo} non trovata nell'ordine {numero_ordine}."
            s.delete(riga)
            s.commit()
        return f"Riga **{codice_articolo}** rimossa dall'ordine {numero_ordine} ✓"

    def dettaglio_ordine(self, numero_ordine: str) -> str:
        """Mostra le righe e il totale di un ordine."""
        with get_session() as s:
            ordine = s.query(Ordine).filter_by(numero=numero_ordine).first()
            if not ordine:
                return f"Errore: ordine {numero_ordine} non trovato."
            righe = s.query(RigaOrdine).filter_by(ordine_id=ordine.id).all()
            header = (
                f"**Ordine {ordine.numero}** – {ordine.cliente.ragione_sociale}\n"
                f"Data: {ordine.data}  |  Stato: {ordine.stato.value}\n\n"
            )
            # indirizzo spedizione cliente
            addr = next(
                (i for i in ordine.cliente.indirizzi if i.tipo.value == "spedizione"),
                next((i for i in ordine.cliente.indirizzi if i.tipo.value == "sede_legale"), None)
            )
            if addr:
                header += f"Spedizione: {addr.via}, {addr.cap} {addr.citta} ({addr.provincia})\n\n"
            header += (
                f"| Codice | Descrizione | Qtà | Prezzo | Subtotale |\n"
                f"|--------|-------------|-----|--------|-----------|\n"
            )
            if not righe:
                return header + "_Nessuna riga._"
            rows = "\n".join(
                f"| {r.articolo.codice} | {r.articolo.descrizione} | {r.quantita} | €{r.prezzo_unitario:.2f} | €{r.quantita * r.prezzo_unitario:.2f} |"
                for r in righe
            )
            totale = sum(r.quantita * r.prezzo_unitario for r in righe)
        return header + rows + f"\n\n**Totale: €{totale:.2f}**"

    def lista_ordini(self, stato: str = None) -> str:
        """Elenca gli ordini, opzionalmente filtrati per stato (bozza/confermato/spedito/chiuso)."""
        with get_session() as s:
            q = s.query(Ordine)
            if stato:
                try:
                    q = q.filter(Ordine.stato == StatoOrdine(stato))
                except ValueError:
                    return f"Errore: stato '{stato}' non valido. Valori: bozza, confermato, spedito, chiuso."
            ordini = q.order_by(Ordine.numero).all()
            if not ordini:
                return "Nessun ordine trovato."
            rows = "\n".join(
                f"| {o.numero} | {o.data} | {o.cliente.ragione_sociale} | {o.stato.value} |"
                for o in ordini
            )
        return f"| Numero | Data | Cliente | Stato |\n|--------|------|---------|-------|\n{rows}"

    def aggiorna_stato_ordine(self, numero_ordine: str, nuovo_stato: str) -> str:
        """Aggiorna lo stato di un ordine (bozza → confermato → spedito → chiuso)."""
        with get_session() as s:
            ordine = s.query(Ordine).filter_by(numero=numero_ordine).first()
            if not ordine:
                return f"Errore: ordine {numero_ordine} non trovato."
            try:
                ordine.stato = StatoOrdine(nuovo_stato)
            except ValueError:
                return f"Errore: stato '{nuovo_stato}' non valido. Valori: bozza, confermato, spedito, chiuso."
            s.commit()
        return f"Ordine **{numero_ordine}** → stato **{nuovo_stato}** ✓"

    # ── REPORT ────────────────────────────────────────────────────────────────

    def vendite_per_cliente(self) -> str:
        """Mostra il totale vendite (somma righe ordini) per cliente."""
        with get_session() as s:
            risultati = (
                s.query(
                    Cliente.codice,
                    Cliente.ragione_sociale,
                    func.sum(RigaOrdine.quantita * RigaOrdine.prezzo_unitario).label("totale"),
                )
                .join(Ordine, Ordine.cliente_id == Cliente.id)
                .join(RigaOrdine, RigaOrdine.ordine_id == Ordine.id)
                .group_by(Cliente.id)
                .order_by(func.sum(RigaOrdine.quantita * RigaOrdine.prezzo_unitario).desc())
                .all()
            )
            if not risultati:
                return "Nessuna vendita registrata."
            rows = "\n".join(f"| {r.codice} | {r.ragione_sociale} | €{r.totale:.2f} |" for r in risultati)
        return f"| Codice | Cliente | Totale |\n|--------|---------|--------|\n{rows}"

    def articoli_sotto_soglia(self, soglia: int) -> str:
        """Elenca gli articoli con giacenza inferiore alla soglia indicata."""
        with get_session() as s:
            articoli = (
                s.query(Articolo)
                .filter(Articolo.giacenza < soglia)
                .order_by(Articolo.giacenza)
                .all()
            )
            if not articoli:
                return f"Nessun articolo con giacenza sotto {soglia}."
            rows = "\n".join(
                f"| {a.codice} | {a.descrizione} | {a.giacenza} |"
                for a in articoli
            )
        return f"| Codice | Descrizione | Giacenza |\n|--------|-------------|----------|\n{rows}"

    # ── FORNITORI ─────────────────────────────────────────────────────────────

    def crea_fornitore(self, codice: str, ragione_sociale: str, email: str = "",
                       telefono: str = "", sito_web: str = "", settore: str = "") -> str:
        """Crea un nuovo fornitore nel database."""
        with get_session() as s:
            if s.query(Fornitore).filter_by(codice=codice).first():
                return f"Errore: esiste già un fornitore con codice {codice}."
            s.add(Fornitore(
                codice=codice, ragione_sociale=ragione_sociale,
                email=email, telefono=telefono, sito_web=sito_web, settore=settore,
            ))
            s.commit()
        return f"Fornitore **{codice} – {ragione_sociale}** creato ✓"

    def lista_fornitori(self) -> str:
        """Restituisce la lista di tutti i fornitori."""
        with get_session() as s:
            fornitori = s.query(Fornitore).order_by(Fornitore.codice).all()
            if not fornitori:
                return "Nessun fornitore presente."
            rows = "\n".join(
                f"| {f.codice} | {f.ragione_sociale} | {f.settore} | {f.sito_web} |"
                for f in fornitori
            )
        return f"| Codice | Ragione Sociale | Settore | Sito Web |\n|--------|-----------------|---------|----------|\n{rows}"

    def cerca_fornitore(self, testo: str) -> str:
        """Cerca fornitori per codice, ragione sociale o settore (ricerca parziale)."""
        with get_session() as s:
            like = f"%{testo}%"
            fornitori = s.query(Fornitore).filter(
                or_(
                    Fornitore.codice.ilike(like),
                    Fornitore.ragione_sociale.ilike(like),
                    Fornitore.settore.ilike(like),
                )
            ).all()
            if not fornitori:
                return f"Nessun fornitore trovato per '{testo}'."
            rows = "\n".join(
                f"| {f.codice} | {f.ragione_sociale} | {f.settore} | {f.sito_web} |"
                for f in fornitori
            )
        return f"| Codice | Ragione Sociale | Settore | Sito Web |\n|--------|-----------------|---------|----------|\n{rows}"

    def aggiorna_fornitore(self, codice: str, ragione_sociale: str = None, email: str = None,
                           telefono: str = None, sito_web: str = None, settore: str = None) -> str:
        """Aggiorna i dati di un fornitore esistente."""
        with get_session() as s:
            f = s.query(Fornitore).filter_by(codice=codice).first()
            if not f:
                return f"Errore: fornitore {codice} non trovato."
            if ragione_sociale is not None:
                f.ragione_sociale = ragione_sociale
            if email is not None:
                f.email = email
            if telefono is not None:
                f.telefono = telefono
            if sito_web is not None:
                f.sito_web = sito_web
            if settore is not None:
                f.settore = settore
            s.commit()
        return f"Fornitore **{codice}** aggiornato ✓"

    def aggiungi_indirizzo_fornitore(self, codice_fornitore: str, tipo: str, via: str,
                                     cap: str, citta: str, provincia: str,
                                     paese: str = "IT", note: str = "") -> str:
        """Aggiunge un indirizzo (sede_legale/spedizione/fatturazione/altro) a un fornitore."""
        with get_session() as s:
            f = s.query(Fornitore).filter_by(codice=codice_fornitore).first()
            if not f:
                return f"Errore: fornitore {codice_fornitore} non trovato."
            try:
                t = TipoIndirizzo(tipo)
            except ValueError:
                return f"Errore: tipo '{tipo}' non valido. Valori: sede_legale, spedizione, fatturazione, altro."
            s.add(Indirizzo(tipo=t, via=via, cap=cap, citta=citta,
                            provincia=provincia, paese=paese, note=note, fornitore_id=f.id))
            s.commit()
        return f"Indirizzo **{tipo}** aggiunto al fornitore {codice_fornitore} ✓"

    def lista_indirizzi_fornitore(self, codice_fornitore: str) -> str:
        """Mostra tutti gli indirizzi di un fornitore."""
        with get_session() as s:
            f = s.query(Fornitore).filter_by(codice=codice_fornitore).first()
            if not f:
                return f"Errore: fornitore {codice_fornitore} non trovato."
            if not f.indirizzi:
                return f"Nessun indirizzo per il fornitore {codice_fornitore}."
            rows = "\n".join(
                f"| {i.tipo.value} | {i.via} | {i.cap} {i.citta} ({i.provincia}) | {i.paese} |"
                for i in f.indirizzi
            )
        return f"| Tipo | Via | Città | Paese |\n|------|-----|-------|-------|\n{rows}"

    def lista_cataloghi_fornitore(self, codice_fornitore: str) -> str:
        """Elenca i cataloghi scaricati per un fornitore."""
        with get_session() as s:
            f = s.query(Fornitore).filter_by(codice=codice_fornitore).first()
            if not f:
                return f"Errore: fornitore {codice_fornitore} non trovato."
            if not f.cataloghi:
                return f"Nessun catalogo scaricato per {codice_fornitore}."
            rows = "\n".join(
                f"| {c.id} | {c.data_scarico} | {c.percorso_file} | {c.url_originale} |"
                for c in f.cataloghi
            )
        return f"| ID | Data | File | URL Originale |\n|----|------|------|---------------|\n{rows}"

    # ── CATEGORIE ─────────────────────────────────────────────────────────────

    def crea_categoria(self, nome: str) -> str:
        """Crea una nuova categoria articoli. Usa prima lista_categorie per evitare duplicati."""
        with get_session() as s:
            if s.query(Categoria).filter_by(nome=nome).first():
                return f"Errore: la categoria **{nome}** esiste già."
            s.add(Categoria(nome=nome))
            s.commit()
        return f"Categoria **{nome}** creata ✓"

    def lista_categorie(self) -> str:
        """Restituisce l'elenco di tutte le categorie articoli disponibili."""
        with get_session() as s:
            cats = s.query(Categoria).order_by(Categoria.nome).all()
            if not cats:
                return "Nessuna categoria presente."
            rows = "\n".join(f"- {c.nome}" for c in cats)
        return f"**Categorie disponibili:**\n{rows}"

    def assegna_categoria(self, codice_articolo: str, nome_categoria: str) -> str:
        """Assegna una categoria a un articolo esistente."""
        with get_session() as s:
            articolo = s.query(Articolo).filter_by(codice=codice_articolo).first()
            if not articolo:
                return f"Errore: articolo **{codice_articolo}** non trovato."
            categoria = s.query(Categoria).filter_by(nome=nome_categoria).first()
            if not categoria:
                return f"Errore: categoria **{nome_categoria}** non trovata. Usa crea_categoria prima."
            articolo.categoria_id = categoria.id
            s.commit()
        return f"Articolo **{codice_articolo}** assegnato alla categoria **{nome_categoria}** ✓"

    def articoli_sotto_scorta_minima(self) -> str:
        """Restituisce gli articoli con giacenza inferiore alla scorta minima impostata. Usare per decidere quando riordinare dal fornitore."""
        with get_session() as s:
            articoli = (
                s.query(Articolo)
                .filter(Articolo.scorta_minima > 0)
                .filter(Articolo.giacenza < Articolo.scorta_minima)
                .order_by(Articolo.codice)
                .all()
            )
            if not articoli:
                return "Nessun articolo sotto scorta minima."
            rows = "\n".join(
                f"| {a.codice} | {a.descrizione} | {a.giacenza} | {a.scorta_minima} |"
                for a in articoli
            )
        return f"**Articoli da riordinare (giacenza < scorta minima):**\n\n| Codice | Descrizione | Giacenza | Scorta Min |\n|--------|-------------|----------|------------|\n{rows}"
