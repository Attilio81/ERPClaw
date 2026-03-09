"""SQLAdmin web panel for ERPClaw — run with: uvicorn erpclaw.web:app --reload"""

from fastapi import FastAPI
from sqladmin import Admin, ModelView

from erpclaw.erp_db import engine, init_db, Articolo, Cliente, Ordine, RigaOrdine, Fornitore, CatalogoFornitore

init_db()

app = FastAPI(title="ERPClaw Admin")
admin = Admin(app, engine, title="ERPClaw")


class ArticoloAdmin(ModelView, model=Articolo):
    name = "Articolo"
    name_plural = "Articoli"
    icon = "fa-solid fa-box"
    column_list = [Articolo.codice, Articolo.descrizione, Articolo.prezzo, Articolo.giacenza]
    column_searchable_list = [Articolo.codice, Articolo.descrizione]
    column_sortable_list = [Articolo.codice, Articolo.prezzo, Articolo.giacenza]


class ClienteAdmin(ModelView, model=Cliente):
    name = "Cliente"
    name_plural = "Clienti"
    icon = "fa-solid fa-users"
    column_list = [Cliente.codice, Cliente.ragione_sociale, Cliente.email, Cliente.telefono]
    column_searchable_list = [Cliente.codice, Cliente.ragione_sociale]
    column_sortable_list = [Cliente.codice, Cliente.ragione_sociale]


class OrdineAdmin(ModelView, model=Ordine):
    name = "Ordine"
    name_plural = "Ordini"
    icon = "fa-solid fa-file-invoice"
    column_list = [Ordine.numero, Ordine.data, Ordine.cliente, Ordine.stato]
    column_searchable_list = [Ordine.numero]
    column_sortable_list = [Ordine.numero, Ordine.data, Ordine.stato]


class RigaOrdineAdmin(ModelView, model=RigaOrdine):
    name = "Riga Ordine"
    name_plural = "Righe Ordine"
    icon = "fa-solid fa-list"
    column_list = [RigaOrdine.ordine, RigaOrdine.articolo, RigaOrdine.quantita, RigaOrdine.prezzo_unitario]


class FornitoreAdmin(ModelView, model=Fornitore):
    name = "Fornitore"
    name_plural = "Fornitori"
    icon = "fa-solid fa-truck"
    column_list = [Fornitore.codice, Fornitore.ragione_sociale, Fornitore.settore, Fornitore.sito_web, Fornitore.email]
    column_searchable_list = [Fornitore.codice, Fornitore.ragione_sociale, Fornitore.settore]
    column_sortable_list = [Fornitore.codice, Fornitore.ragione_sociale, Fornitore.settore]


class CatalogoFornitoreAdmin(ModelView, model=CatalogoFornitore):
    name = "Catalogo Fornitore"
    name_plural = "Cataloghi Fornitori"
    icon = "fa-solid fa-file-pdf"
    column_list = [CatalogoFornitore.fornitore, CatalogoFornitore.data_scarico, CatalogoFornitore.percorso_file, CatalogoFornitore.url_originale]
    column_sortable_list = [CatalogoFornitore.data_scarico]


admin.add_view(ArticoloAdmin)
admin.add_view(ClienteAdmin)
admin.add_view(OrdineAdmin)
admin.add_view(RigaOrdineAdmin)
admin.add_view(FornitoreAdmin)
admin.add_view(CatalogoFornitoreAdmin)
