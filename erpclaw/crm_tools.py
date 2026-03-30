"""Agno Toolkit with CRM tools for customer events, notes, and agenda management."""

from datetime import datetime, date, timedelta

from agno.tools import Toolkit

from erpclaw.erp_db import (
    get_session, init_db,
    EventoCRM, NotaCRM, Cliente,
    TipoEventoCRM, StatoEventoCRM,
)

init_db()


class CrmTools(Toolkit):
    def __init__(self):
        super().__init__(name="crm_tools")
        self.register(self.crea_evento)
        self.register(self.lista_eventi)
        self.register(self.agenda_oggi)
        self.register(self.agenda_settimana)
        self.register(self.aggiorna_evento)
        self.register(self.completa_evento)
        self.register(self.annulla_evento)
        self.register(self.aggiungi_nota)
        self.register(self.note_cliente)
        self.register(self.storico_cliente)

    # ── EVENTI ────────────────────────────────────────────────────────────────

    def crea_evento(
        self,
        tipo: str,
        data_ora: str,
        cliente_id: int = None,
        luogo: str = None,
        note: str = None,
        durata_minuti: int = None,
    ) -> str:
        """Crea un nuovo evento CRM (visita, chiamata o email).
        tipo: visita/chiamata/email. data_ora in formato ISO (es. 2026-04-01 10:30).
        cliente_id è opzionale."""
        try:
            tipo_enum = TipoEventoCRM(tipo)
        except ValueError:
            return f"Errore: tipo '{tipo}' non valido. Valori: visita, chiamata, email."
        try:
            dt = datetime.fromisoformat(data_ora)
        except ValueError:
            return f"Errore: data_ora '{data_ora}' non valida. Formato: YYYY-MM-DD HH:MM"
        with get_session() as s:
            ev = EventoCRM(
                tipo=tipo_enum,
                data_ora=dt,
                cliente_id=cliente_id,
                luogo=luogo,
                note=note,
                durata_minuti=durata_minuti,
                stato=StatoEventoCRM.pianificato,
                reminder_inviato=False,
            )
            s.add(ev)
            s.flush()
            ev_id = ev.id
            cliente_nome = ev.cliente.ragione_sociale if ev.cliente else "—"
            s.commit()
        return f"Evento **{tipo}** creato (ID {ev_id}) per {cliente_nome} il {dt.strftime('%d/%m/%Y %H:%M')} ✓"

    def _format_eventi(self, eventi) -> str:
        if not eventi:
            return "Nessun evento."
        rows = "\n".join(
            f"| {ev.id} | {ev.tipo.value} | "
            f"{ev.cliente.ragione_sociale if ev.cliente else '—'} | "
            f"{ev.data_ora.strftime('%d/%m/%Y %H:%M')} | {ev.stato.value} | "
            f"{ev.luogo or '—'} |"
            for ev in eventi
        )
        return (
            "| ID | Tipo | Cliente | Data/Ora | Stato | Luogo |\n"
            "|-----|------|---------|----------|-------|-------|\n"
            + rows
        )

    def lista_eventi(self, data_inizio: str, data_fine: str, cliente_id: int = None) -> str:
        """Elenca gli eventi CRM in un intervallo di date (formato YYYY-MM-DD).
        Filtra opzionalmente per cliente_id."""
        try:
            d1 = datetime.fromisoformat(data_inizio)
            d2 = datetime.fromisoformat(data_fine)
            if len(data_fine.strip()) == 10:  # solo data senza orario → fine giornata
                d2 = d2.replace(hour=23, minute=59, second=59)
        except ValueError:
            return "Errore: date non valide. Formato: YYYY-MM-DD"
        with get_session() as s:
            q = s.query(EventoCRM).filter(
                EventoCRM.data_ora >= d1,
                EventoCRM.data_ora <= d2,
            )
            if cliente_id:
                q = q.filter(EventoCRM.cliente_id == cliente_id)
            eventi = q.order_by(EventoCRM.data_ora).all()
            return self._format_eventi(eventi)

    def agenda_oggi(self) -> str:
        """Mostra tutti gli eventi CRM pianificati per oggi."""
        oggi = date.today()
        d1 = datetime(oggi.year, oggi.month, oggi.day, 0, 0, 0)
        d2 = datetime(oggi.year, oggi.month, oggi.day, 23, 59, 59)
        with get_session() as s:
            eventi = (
                s.query(EventoCRM)
                .filter(EventoCRM.data_ora >= d1, EventoCRM.data_ora <= d2)
                .order_by(EventoCRM.data_ora)
                .all()
            )
            return self._format_eventi(eventi)

    def agenda_settimana(self) -> str:
        """Mostra gli eventi CRM pianificati per i prossimi 7 giorni."""
        d1 = datetime.now()
        d2 = d1 + timedelta(days=7)
        with get_session() as s:
            eventi = (
                s.query(EventoCRM)
                .filter(EventoCRM.data_ora >= d1, EventoCRM.data_ora <= d2)
                .order_by(EventoCRM.data_ora)
                .all()
            )
            return self._format_eventi(eventi)

    def aggiorna_evento(
        self,
        evento_id: int,
        tipo: str = None,
        data_ora: str = None,
        luogo: str = None,
        note: str = None,
        durata_minuti: int = None,
        esito: str = None,
    ) -> str:
        """Aggiorna i campi di un evento CRM esistente. Passare solo i campi da modificare.
        Se data_ora viene modificata, il reminder viene resettato."""
        with get_session() as s:
            ev = s.get(EventoCRM, evento_id)
            if not ev:
                return f"Errore: evento {evento_id} non trovato."
            if tipo is not None:
                try:
                    ev.tipo = TipoEventoCRM(tipo)
                except ValueError:
                    return f"Errore: tipo '{tipo}' non valido."
            if data_ora is not None:
                try:
                    ev.data_ora = datetime.fromisoformat(data_ora)
                    ev.reminder_inviato = False
                except ValueError:
                    return f"Errore: data_ora '{data_ora}' non valida."
            if luogo is not None:
                ev.luogo = luogo
            if note is not None:
                ev.note = note
            if durata_minuti is not None:
                ev.durata_minuti = durata_minuti
            if esito is not None:
                ev.esito = esito
            s.commit()
        return f"Evento {evento_id} aggiornato ✓"

    def completa_evento(self, evento_id: int, esito: str, note: str = None) -> str:
        """Segna un evento CRM come completato registrando l'esito."""
        with get_session() as s:
            ev = s.get(EventoCRM, evento_id)
            if not ev:
                return f"Errore: evento {evento_id} non trovato."
            ev.stato = StatoEventoCRM.completato
            ev.esito = esito
            if note is not None:
                ev.note = note
            s.commit()
        return f"Evento {evento_id} completato: {esito} ✓"

    def annulla_evento(self, evento_id: int) -> str:
        """Annulla un evento CRM pianificato."""
        with get_session() as s:
            ev = s.get(EventoCRM, evento_id)
            if not ev:
                return f"Errore: evento {evento_id} non trovato."
            ev.stato = StatoEventoCRM.annullato
            s.commit()
        return f"Evento {evento_id} annullato ✓"

    # ── NOTE ──────────────────────────────────────────────────────────────────

    def aggiungi_nota(self, cliente_id: int, testo: str) -> str:
        """Aggiunge una nota libera a un cliente nel CRM."""
        with get_session() as s:
            c = s.get(Cliente, cliente_id)
            if not c:
                return f"Errore: cliente {cliente_id} non trovato."
            nota = NotaCRM(cliente_id=cliente_id, testo=testo, data_ora=datetime.now())
            s.add(nota)
            s.commit()
            nota_id = nota.id
        return f"Nota aggiunta al cliente {cliente_id} (ID nota {nota_id}) ✓"

    def note_cliente(self, cliente_id: int) -> str:
        """Mostra tutte le note CRM di un cliente, ordinate per data decrescente."""
        with get_session() as s:
            c = s.get(Cliente, cliente_id)
            if not c:
                return f"Errore: cliente {cliente_id} non trovato."
            note = (
                s.query(NotaCRM)
                .filter_by(cliente_id=cliente_id)
                .order_by(NotaCRM.data_ora.desc())
                .all()
            )
            if not note:
                return f"Nessuna nota per il cliente {cliente_id}."
            rows = "\n".join(
                f"| {n.id} | {n.data_ora.strftime('%d/%m/%Y %H:%M')} | {n.testo[:80]} |"
                for n in note
            )
        return (
            f"**Note del cliente {cliente_id}:**\n"
            "| ID | Data | Testo |\n|----|------|-------|\n"
            + rows
        )

    # ── STORICO ───────────────────────────────────────────────────────────────

    def storico_cliente(self, cliente_id: int) -> str:
        """Mostra lo storico CRM completo di un cliente: tutti gli eventi e le note."""
        with get_session() as s:
            c = s.get(Cliente, cliente_id)
            if not c:
                return f"Errore: cliente {cliente_id} non trovato."
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
            ragione = c.ragione_sociale

            result = f"## Storico CRM — {ragione}\n\n"
            if eventi:
                rows = "\n".join(
                    f"| {ev.id} | {ev.tipo.value} | {ev.data_ora.strftime('%d/%m/%Y %H:%M')} | "
                    f"{ev.stato.value} | {ev.esito or '—'} |"
                    for ev in eventi
                )
                result += (
                    "### 📅 Eventi\n"
                    "| ID | Tipo | Data/Ora | Stato | Esito |\n"
                    "|----|------|----------|-------|-------|\n"
                    + rows + "\n\n"
                )
            else:
                result += "### 📅 Eventi\nNessun evento.\n\n"

            if note:
                rows = "\n".join(
                    f"| {n.id} | {n.data_ora.strftime('%d/%m/%Y %H:%M')} | {n.testo[:100]} |"
                    for n in note
                )
                result += (
                    "### 📝 Note\n"
                    "| ID | Data | Testo |\n|----|------|-------|\n"
                    + rows
                )
            else:
                result += "### 📝 Note\nNessuna nota."

            return result
