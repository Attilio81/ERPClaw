"""Toolkit for supplier web research and catalog download/parsing."""

import pathlib
from datetime import date

import httpx
import pdfplumber
from agno.tools import Toolkit

from erpclaw.erp_db import get_session, Fornitore, CatalogoFornitore

CATALOGHI_DIR = pathlib.Path("./cataloghi")


class FornitoreResearchTools(Toolkit):
    def __init__(self):
        super().__init__(name="fornitore_research")
        CATALOGHI_DIR.mkdir(exist_ok=True)
        self.register(self.scarica_catalogo)
        self.register(self.leggi_catalogo)
        self.register(self.elimina_catalogo)

    def scarica_catalogo(self, url: str, codice_fornitore: str, note: str = "") -> str:
        """Scarica un PDF catalogo da URL e lo salva localmente, associandolo al fornitore."""
        with get_session() as s:
            fornitore = s.query(Fornitore).filter_by(codice=codice_fornitore).first()
            if not fornitore:
                return f"Errore: fornitore {codice_fornitore} non trovato nel database."

            try:
                response = httpx.get(url, follow_redirects=True, timeout=30)
                response.raise_for_status()
            except httpx.HTTPError as e:
                return f"Errore download: {e}"

            content_type = response.headers.get("content-type", "")
            if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
                return f"Errore: l'URL non sembra puntare a un PDF (content-type: {content_type})."

            filename = f"{codice_fornitore}_{date.today().isoformat()}_{len(fornitore.cataloghi) + 1}.pdf"
            filepath = CATALOGHI_DIR / filename
            filepath.write_bytes(response.content)

            catalogo = CatalogoFornitore(
                fornitore_id=fornitore.id,
                url_originale=url,
                percorso_file=str(filepath),
                data_scarico=date.today(),
                note=note,
            )
            s.add(catalogo)
            s.commit()
            catalogo_id = catalogo.id

        return (
            f"Catalogo scaricato ✓\n"
            f"- File: `{filepath}`\n"
            f"- ID catalogo: {catalogo_id}\n"
            f"- Dimensione: {len(response.content) / 1024:.1f} KB\n"
            f"Usa `leggi_catalogo` per estrarne il contenuto."
        )

    def leggi_catalogo(self, id_catalogo: int, pagine: str = "") -> str:
        """Estrae il testo da un catalogo PDF scaricato. Specifica 'pagine' come range es. '1-5' o '3'."""
        with get_session() as s:
            catalogo = s.query(CatalogoFornitore).filter_by(id=id_catalogo).first()
            if not catalogo:
                return f"Errore: catalogo ID {id_catalogo} non trovato."
            filepath = catalogo.percorso_file
            fornitore_nome = catalogo.fornitore.ragione_sociale

        path = pathlib.Path(filepath)
        if not path.exists():
            return f"Errore: file `{filepath}` non trovato su disco."

        # Determina pagine da estrarre
        page_filter: set[int] | None = None
        if pagine:
            page_filter = set()
            for part in pagine.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = part.split("-")
                    page_filter.update(range(int(start) - 1, int(end)))
                else:
                    page_filter.add(int(part) - 1)

        try:
            with pdfplumber.open(path) as pdf:
                total = len(pdf.pages)
                pages_to_read = (
                    [pdf.pages[i] for i in sorted(page_filter) if i < total]
                    if page_filter else pdf.pages[:20]  # massimo 20 pagine di default
                )
                testo = "\n\n".join(
                    f"--- Pagina {pdf.pages.index(p) + 1} ---\n{p.extract_text() or '(nessun testo)'}"
                    for p in pages_to_read
                )
        except Exception as e:
            return f"Errore lettura PDF: {e}"

        troncato = len(pages_to_read) < total and not page_filter
        avviso = f"\n\n_(mostrate prime 20 di {total} pagine — specifica `pagine` per leggere altre)_" if troncato else ""
        return f"**Catalogo {fornitore_nome}** (ID {id_catalogo})\n\n{testo}{avviso}"

    def elimina_catalogo(self, id_catalogo: int) -> str:
        """Elimina un catalogo dal database e dal disco."""
        with get_session() as s:
            catalogo = s.query(CatalogoFornitore).filter_by(id=id_catalogo).first()
            if not catalogo:
                return f"Errore: catalogo ID {id_catalogo} non trovato."
            filepath = pathlib.Path(catalogo.percorso_file)
            s.delete(catalogo)
            s.commit()

        if filepath.exists():
            filepath.unlink()
        return f"Catalogo ID {id_catalogo} eliminato ✓"
