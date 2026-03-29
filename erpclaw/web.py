"""SQLAdmin web panel for ERPClaw — run with: uvicorn erpclaw.web:app --reload"""

from fastapi import FastAPI
from sqladmin import Admin, ModelView

from erpclaw.erp_db import (
    engine, init_db,
    Categoria, Articolo, Cliente, Ordine, RigaOrdine, Fornitore, CatalogoFornitore,
    Indirizzo,
    Magazzino, Zona, Scaffale, Ripiano, StockUbicazione, MovimentoMagazzino,
    OrdineFornitore, RigaOrdineFornitore,
)

init_db()

app = FastAPI(title="ERPClaw Admin")

from erpclaw.shop import router as shop_router
from erpclaw.chat import router as chat_router
from erpclaw.agents_dashboard import router as agents_router
from erpclaw.config_panel import router as config_router
app.include_router(shop_router)
app.include_router(chat_router)
app.include_router(agents_router)
app.include_router(config_router)

admin = Admin(app, engine, title="ERPClaw")


class CategoriaAdmin(ModelView, model=Categoria):
    name = "Categoria"
    name_plural = "Categorie"
    icon = "fa-solid fa-tag"
    column_list = [Categoria.nome]
    column_searchable_list = [Categoria.nome]
    column_sortable_list = [Categoria.nome]


class ArticoloAdmin(ModelView, model=Articolo):
    name = "Articolo"
    name_plural = "Articoli"
    icon = "fa-solid fa-box"
    column_list = [Articolo.codice, Articolo.descrizione, Articolo.categoria, Articolo.prezzo_vendita, Articolo.prezzo_acquisto, Articolo.giacenza, Articolo.scorta_minima]
    column_searchable_list = [Articolo.codice, Articolo.descrizione]
    column_sortable_list = [Articolo.codice, Articolo.prezzo_vendita, Articolo.giacenza]
    form_excluded_columns = ["giacenza"]
    page_size = 100
    page_size_options = [25, 50, 100, 200]


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
    column_list = [Ordine.numero, Ordine.data, Ordine.stato, Ordine.cliente]
    column_searchable_list = [Ordine.numero]
    column_sortable_list = [Ordine.numero, Ordine.data, Ordine.stato]
    column_details_list = [Ordine.numero, Ordine.data, Ordine.stato, Ordine.cliente, Ordine.righe]


class RigaOrdineAdmin(ModelView, model=RigaOrdine):
    name = "Riga Ordine"
    name_plural = "Righe Ordine"
    icon = "fa-solid fa-list"
    column_list = [RigaOrdine.ordine, RigaOrdine.articolo, RigaOrdine.quantita, RigaOrdine.prezzo_unitario]
    column_sortable_list = [RigaOrdine.quantita, RigaOrdine.prezzo_unitario]


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


class OrdineFornitoreAdmin(ModelView, model=OrdineFornitore):
    name = "Ordine Fornitore"
    name_plural = "Ordini Fornitori"
    icon = "fa-solid fa-truck-ramp-box"
    column_list = [OrdineFornitore.numero, OrdineFornitore.data, OrdineFornitore.fornitore, OrdineFornitore.stato]
    column_searchable_list = [OrdineFornitore.numero]
    column_sortable_list = [OrdineFornitore.numero, OrdineFornitore.data, OrdineFornitore.stato]
    column_details_list = [OrdineFornitore.numero, OrdineFornitore.data, OrdineFornitore.stato, OrdineFornitore.fornitore, OrdineFornitore.righe, OrdineFornitore.note]


class RigaOrdineFornitoreAdmin(ModelView, model=RigaOrdineFornitore):
    name = "Riga Ordine Fornitore"
    name_plural = "Righe Ordini Fornitori"
    icon = "fa-solid fa-list"
    column_list = [RigaOrdineFornitore.ordine_fornitore, RigaOrdineFornitore.articolo, RigaOrdineFornitore.quantita, RigaOrdineFornitore.prezzo_unitario]
    column_sortable_list = [RigaOrdineFornitore.quantita, RigaOrdineFornitore.prezzo_unitario]


class IndirizzoAdmin(ModelView, model=Indirizzo):
    name = "Indirizzo"
    name_plural = "Indirizzi"
    icon = "fa-solid fa-map-marker-alt"
    column_list = [Indirizzo.tipo, Indirizzo.via, Indirizzo.citta, Indirizzo.cap, Indirizzo.paese]
    column_searchable_list = [Indirizzo.citta, Indirizzo.cap]
    column_sortable_list = [Indirizzo.tipo, Indirizzo.citta]


class MagazzinoAdmin(ModelView, model=Magazzino):
    name = "Magazzino"
    name_plural = "Magazzini"
    icon = "fa-solid fa-warehouse"
    column_list = [Magazzino.codice, Magazzino.nome]
    column_searchable_list = [Magazzino.codice, Magazzino.nome]


class ZonaAdmin(ModelView, model=Zona):
    name = "Zona"
    name_plural = "Zone"
    icon = "fa-solid fa-layer-group"
    column_list = [Zona.codice, Zona.nome, Zona.magazzino]
    column_searchable_list = [Zona.codice, Zona.nome]


class ScaffaleAdmin(ModelView, model=Scaffale):
    name = "Scaffale"
    name_plural = "Scaffali"
    icon = "fa-solid fa-th-large"
    column_list = [Scaffale.codice, Scaffale.nome, Scaffale.zona]
    column_searchable_list = [Scaffale.codice, Scaffale.nome]


class RipianoAdmin(ModelView, model=Ripiano):
    name = "Ripiano"
    name_plural = "Ripiani"
    icon = "fa-solid fa-bars"
    column_list = [Ripiano.codice, Ripiano.nome, Ripiano.scaffale]
    column_searchable_list = [Ripiano.codice, Ripiano.nome]


class StockUbicazioneAdmin(ModelView, model=StockUbicazione):
    name = "Stock Ubicazione"
    name_plural = "Stock Ubicazioni"
    icon = "fa-solid fa-cubes"
    column_list = [StockUbicazione.articolo, StockUbicazione.ripiano, StockUbicazione.quantita]
    column_sortable_list = [StockUbicazione.quantita]


class MovimentoMagazzinoAdmin(ModelView, model=MovimentoMagazzino):
    name = "Movimento Magazzino"
    name_plural = "Movimenti Magazzino"
    icon = "fa-solid fa-arrows-alt"
    column_list = [MovimentoMagazzino.data_ora, MovimentoMagazzino.tipo, MovimentoMagazzino.articolo,
                   MovimentoMagazzino.quantita, MovimentoMagazzino.ordine]
    column_sortable_list = [MovimentoMagazzino.data_ora, MovimentoMagazzino.tipo]


admin.add_view(CategoriaAdmin)
admin.add_view(ArticoloAdmin)
admin.add_view(ClienteAdmin)
admin.add_view(OrdineAdmin)
admin.add_view(RigaOrdineAdmin)
admin.add_view(FornitoreAdmin)
admin.add_view(CatalogoFornitoreAdmin)
admin.add_view(OrdineFornitoreAdmin)
admin.add_view(RigaOrdineFornitoreAdmin)
admin.add_view(IndirizzoAdmin)
admin.add_view(MagazzinoAdmin)
admin.add_view(ZonaAdmin)
admin.add_view(ScaffaleAdmin)
admin.add_view(RipianoAdmin)
admin.add_view(StockUbicazioneAdmin)
admin.add_view(MovimentoMagazzinoAdmin)
