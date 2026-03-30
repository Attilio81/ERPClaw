"""Persistent JSON configuration for the agent team.

Stores agent names, roles, instructions, model settings, tool assignments,
and UI positions for the dashboard.  The canonical config lives in
``agent_config.json`` next to ``erp.db`` (project root).
"""

import json
import pathlib
from typing import Any

CONFIG_PATH = pathlib.Path("agent_config.json")

# ---------------------------------------------------------------------------
# Default configuration (mirrors the hardcoded values in agent.py)
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    "model": {
        "provider": "lmstudio",
        "model_id": "qwen3.5-9b",
        "lmstudio_base_url": "http://localhost:1234/v1",
    },
    "team": {
        "name": "ERPClaw",
        "thinking": True,
        "num_history_runs": 5,
        "tools": ["ERPTools", "LogisticaTools", "CrmTools"],
        "members": ["RicercaFornitore"],
        "instructions": (
            "Sei l'assistente del gestionale aziendale ERPClaw.\n"
            "Gestisci articoli, clienti, ordini e fornitori tramite i tool disponibili.\n"
            "\n"
            "Regole fondamentali:\n"
            "- Rispondi sempre in italiano.\n"
            "- Usa le tabelle markdown per le liste.\n"
            "- Non inventare dati: usa solo i tool per leggere/scrivere il database.\n"
            "- Prima di creare un ordine, verifica che il cliente esista; se non esiste, chiedi se crearlo.\n"
            "- Quando aggiungi righe a un ordine, conferma sempre qtà e prezzo prima di procedere.\n"
            "- Per le operazioni distruttive (rimuovi riga, cambia stato ordine, elimina catalogo) chiedi conferma esplicita.\n"
            "- Se un'operazione va a buon fine, mostra il risultato in modo chiaro e conciso.\n"
            "- Se l'utente chiede report o statistiche, usa i tool appositi (vendite_per_cliente, articoli_sotto_soglia).\n"
            "\n"
            "Gestione fornitori:\n"
            "- Per cercare fornitori online, trovare recensioni o scaricare cataloghi PDF, delega a RicercaFornitore.\n"
            "- Dopo la ricerca online, proponi di salvare il fornitore nel database con crea_fornitore.\n"
            "- Per scaricare un catalogo serve prima che il fornitore esista nel DB.\n"
            "\n"
            "Gestione logistica:\n"
            "- Per ubicare articoli in magazzino usa crea_magazzino, crea_zona, crea_scaffale, crea_ripiano.\n"
            "- Per caricare stock usa assegna_stock; per spostarlo usa trasferisci_stock.\n"
            "- Quando un ordine viene marcato come 'spedito', proponi all'utente di eseguire scarica_ordine_da_ubicazione.\n"
            "- Per verificare dove si trova un articolo usa stock_per_articolo; per vedere cosa c'è in un ripiano usa stock_per_ubicazione.\n"
            "- Segnala proattivamente gli articoli senza ubicazione con articoli_senza_ubicazione.\n"
            "\n"
            "Gestione CRM:\n"
            "- Per pianificare visite, chiamate o email usa crea_evento (tipo: visita/chiamata/email).\n"
            "- Per vedere l'agenda del giorno usa agenda_oggi; per la settimana usa agenda_settimana.\n"
            "- Quando una visita è avvenuta, usa completa_evento con un esito.\n"
            "- Per appunti su un cliente senza data specifica usa aggiungi_nota.\n"
            "- Per vedere tutto lo storico CRM di un cliente usa storico_cliente.\n"
        ),
        "position": {"x": 400, "y": 300},
    },
    "agents": {
        "RicercaFornitore": {
            "name": "RicercaFornitore",
            "role": "Specialista in ricerca fornitori online, recensioni e analisi cataloghi",
            "thinking": True,
            "tools": ["DuckDuckGoTools", "FornitoreResearchTools"],
            "instructions": (
                "Sei uno specialista di ricerca fornitori B2B.\n"
                "- Usa web_search per trovare fornitori per settore/prodotto e per cercare recensioni.\n"
                "- Non usare operatori avanzati come site: nelle query (DuckDuckGo non li supporta); usa invece il nome del sito come termine di ricerca.\n"
                "- Per le recensioni cerca su Google, Trustpilot, forum di settore.\n"
                "- Se ti viene fornito un URL di catalogo PDF, usa scarica_catalogo per salvarlo.\n"
                "- Dopo il download usa leggi_catalogo per estrarne prodotti e prezzi rilevanti.\n"
                "- Presenta i risultati in italiano con tabelle markdown.\n"
                "- Sii critico: segnala se un fornitore ha recensioni negative o scarse informazioni online."
            ),
            "position": {"x": 850, "y": 300},
        }
    },
    "memory_manager": {
        "memory_capture_instructions": (
            "Raccogli il nome dell'utente,\n"
            "Raccogli le preferenze e gli interessi dell'utente,\n"
            "Raccogli informazioni su ciò che piace e non piace all'utente."
        ),
        "position": {"x": 400, "y": 80},
    },
    "tools": {
        "ERPTools": {
            "label": "ERP Tools",
            "description": "Articoli, clienti, ordini, fornitori, categorie, indirizzi",
            "methods": [
                "crea_articolo", "lista_articoli", "cerca_articolo", "aggiorna_articolo",
                "crea_cliente", "lista_clienti", "cerca_cliente", "aggiorna_cliente",
                "crea_ordine", "aggiungi_riga", "rimuovi_riga", "dettaglio_ordine",
                "lista_ordini", "aggiorna_stato_ordine", "vendite_per_cliente",
                "articoli_sotto_soglia", "crea_fornitore", "lista_fornitori",
                "cerca_fornitore", "aggiorna_fornitore", "lista_cataloghi_fornitore",
                "aggiungi_indirizzo_cliente", "aggiungi_indirizzo_fornitore",
                "lista_indirizzi_cliente", "lista_indirizzi_fornitore",
                "crea_categoria", "lista_categorie", "assegna_categoria",
                "articoli_sotto_scorta_minima", "crea_ordine_fornitore",
                "aggiungi_riga_ordine_fornitore", "lista_ordini_fornitori",
                "visualizza_ordine_fornitore", "avanza_stato_ordine_fornitore",
            ],
            "position": {"x": 100, "y": 200},
        },
        "LogisticaTools": {
            "label": "Logistica Tools",
            "description": "Magazzini, zone, scaffali, ripiani, stock, movimenti",
            "methods": [
                "crea_magazzino", "crea_zona", "crea_scaffale", "crea_ripiano",
                "lista_ubicazioni", "assegna_stock", "trasferisci_stock",
                "stock_per_articolo", "stock_per_ubicazione",
                "articoli_senza_ubicazione", "scarica_ordine_da_ubicazione",
                "storico_movimenti",
            ],
            "position": {"x": 100, "y": 450},
        },
        "CrmTools": {
            "label": "CRM Tools",
            "description": "Visite clienti, chiamate, email, note e agenda CRM",
            "methods": [
                "crea_evento", "lista_eventi", "agenda_oggi", "agenda_settimana",
                "aggiorna_evento", "completa_evento", "annulla_evento",
                "aggiungi_nota", "note_cliente", "storico_cliente",
            ],
            "position": {"x": 100, "y": 650},
        },
        "DuckDuckGoTools": {
            "label": "DuckDuckGo Search",
            "description": "Ricerca web tramite DuckDuckGo",
            "methods": ["web_search"],
            "position": {"x": 1200, "y": 200},
        },
        "FornitoreResearchTools": {
            "label": "Fornitore Research",
            "description": "Download e analisi cataloghi PDF fornitori",
            "methods": ["scarica_catalogo", "leggi_catalogo", "elimina_catalogo"],
            "position": {"x": 1200, "y": 450},
        },
    },
}


def load_config() -> dict[str, Any]:
    """Load config from JSON file, creating it with defaults if missing."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    # First run: write defaults
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Persist config to JSON file."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_config() -> dict[str, Any]:
    """Return current config (always fresh from disk)."""
    return load_config()


def update_config(patch: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge *patch* into existing config and save."""
    config = load_config()
    _deep_merge(config, patch)
    save_config(config)
    return config


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
