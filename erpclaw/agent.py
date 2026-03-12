from agno.agent import Agent
from agno.db.sqlite import AsyncSqliteDb
from agno.memory.manager import MemoryManager
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools

from erpclaw.config import DEEPSEEK_API_KEY, LLM_MODEL_ID, LLM_PROVIDER, LMSTUDIO_BASE_URL
from erpclaw.erp_tools import ERPTools
from erpclaw.fornitore_research_tools import FornitoreResearchTools
from erpclaw.logistica_tools import LogisticaTools


def _make_model(thinking: bool = False):
    if LLM_PROVIDER == "deepseek":
        from agno.models.deepseek import DeepSeek
        return DeepSeek(id=LLM_MODEL_ID, api_key=DEEPSEEK_API_KEY)
    else:
        from agno.models.lmstudio import LMStudio
        return LMStudio(
            id=LLM_MODEL_ID,
            base_url=LMSTUDIO_BASE_URL,
            extra_body={"enable_thinking": thinking},
        )


db = AsyncSqliteDb(db_file="./agent.db")

memory_manager = MemoryManager(
    model=_make_model(),
    db=db,
    memory_capture_instructions="""\
        Raccogli il nome dell'utente,
        Raccogli le preferenze e gli interessi dell'utente,
        Raccogli informazioni su ciò che piace e non piace all'utente.
    """
)

# Sub-agente specializzato nella ricerca fornitori online
fornitore_research_agent = Agent(
    name="RicercaFornitore",
    role="Specialista in ricerca fornitori online, recensioni e analisi cataloghi",
    model=_make_model(thinking=True),
    tools=[DuckDuckGoTools(), FornitoreResearchTools()],
    instructions="""\
Sei uno specialista di ricerca fornitori B2B.
- Usa web_search per trovare fornitori per settore/prodotto e per cercare recensioni.
- Non usare operatori avanzati come site: nelle query (DuckDuckGo non li supporta); usa invece il nome del sito come termine di ricerca.
- Per le recensioni cerca su Google, Trustpilot, forum di settore.
- Se ti viene fornito un URL di catalogo PDF, usa scarica_catalogo per salvarlo.
- Dopo il download usa leggi_catalogo per estrarne prodotti e prezzi rilevanti.
- Presenta i risultati in italiano con tabelle markdown.
- Sii critico: segnala se un fornitore ha recensioni negative o scarse informazioni online.
""",
    markdown=True,
)

# Team ERP: agente principale con delega al ricercatore fornitori
team = Team(
    name="ERPClaw",
    model=_make_model(thinking=True),
    tools=[ERPTools(), LogisticaTools()],
    members=[fornitore_research_agent],
    db=db,
    memory_manager=memory_manager,
    enable_agentic_memory=True,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
    debug_mode=True,
    instructions="""\
Sei l'assistente del gestionale aziendale ERPClaw.
Gestisci articoli, clienti, ordini e fornitori tramite i tool disponibili.

Regole fondamentali:
- Rispondi sempre in italiano.
- Usa le tabelle markdown per le liste.
- Non inventare dati: usa solo i tool per leggere/scrivere il database.
- Prima di creare un ordine, verifica che il cliente esista; se non esiste, chiedi se crearlo.
- Quando aggiungi righe a un ordine, conferma sempre qtà e prezzo prima di procedere.
- Per le operazioni distruttive (rimuovi riga, cambia stato ordine, elimina catalogo) chiedi conferma esplicita.
- Se un'operazione va a buon fine, mostra il risultato in modo chiaro e conciso.
- Se l'utente chiede report o statistiche, usa i tool appositi (vendite_per_cliente, articoli_sotto_soglia).

Gestione fornitori:
- Per cercare fornitori online, trovare recensioni o scaricare cataloghi PDF, delega a RicercaFornitore.
- Dopo la ricerca online, proponi di salvare il fornitore nel database con crea_fornitore.
- Per scaricare un catalogo serve prima che il fornitore esista nel DB.

Gestione logistica:
- Per ubicare articoli in magazzino usa crea_magazzino, crea_zona, crea_scaffale, crea_ripiano.
- Per caricare stock usa assegna_stock; per spostarlo usa trasferisci_stock.
- Quando un ordine viene marcato come 'spedito', proponi all'utente di eseguire scarica_ordine_da_ubicazione.
- Per verificare dove si trova un articolo usa stock_per_articolo; per vedere cosa c'è in un ripiano usa stock_per_ubicazione.
- Segnala proattivamente gli articoli senza ubicazione con articoli_senza_ubicazione.
"""
)


import re as _re


def _strip_reasoning(text: str) -> str:
    """Rimuove i tag <reasoning>...</reasoning> che Qwen3.5 inserisce nel testo."""
    return _re.sub(r"<reasoning>.*?</reasoning>", "", text, flags=_re.DOTALL).strip()


async def run_agent(user_message: str, user_id: str = "default_user") -> str:
    """Process a user message through the AI agent and return the response."""
    response = await team.arun(user_message, user_id=user_id)
    return _strip_reasoning(response.content)
