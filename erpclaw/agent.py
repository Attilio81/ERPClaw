from agno.agent import Agent
from agno.db.sqlite import AsyncSqliteDb
from agno.memory.manager import MemoryManager
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools

from erpclaw.agent_config import get_config
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


# ── Tool registry ────────────────────────────────────────────
TOOL_CLASSES = {
    "ERPTools": ERPTools,
    "LogisticaTools": LogisticaTools,
    "DuckDuckGoTools": DuckDuckGoTools,
    "FornitoreResearchTools": FornitoreResearchTools,
}


def _resolve_tools(names: list[str]):
    """Instantiate toolkit objects from their string names."""
    return [TOOL_CLASSES[n]() for n in names if n in TOOL_CLASSES]


# ── Build team from config ────────────────────────────────────
db = AsyncSqliteDb(db_file="./agent.db")


def _build_team(cfg: dict) -> tuple[Team, dict[str, Agent]]:
    """Build the full agent team from a config dict."""
    # Memory manager
    mm = MemoryManager(
        model=_make_model(),
        db=db,
        memory_capture_instructions=cfg["memory_manager"]["memory_capture_instructions"],
    )

    # Sub-agents
    agents: dict[str, Agent] = {}
    for key, acfg in cfg.get("agents", {}).items():
        agents[key] = Agent(
            name=acfg["name"],
            role=acfg["role"],
            model=_make_model(thinking=acfg.get("thinking", True)),
            tools=_resolve_tools(acfg.get("tools", [])),
            instructions=acfg["instructions"],
            markdown=True,
        )

    # Team
    tcfg = cfg["team"]
    t = Team(
        name=tcfg["name"],
        model=_make_model(thinking=tcfg.get("thinking", True)),
        tools=_resolve_tools(tcfg.get("tools", [])),
        members=[agents[m] for m in tcfg.get("members", []) if m in agents],
        db=db,
        memory_manager=mm,
        enable_agentic_memory=True,
        add_history_to_context=True,
        num_history_runs=tcfg.get("num_history_runs", 5),
        add_datetime_to_context=True,
        markdown=True,
        debug_mode=True,
        instructions=tcfg["instructions"],
    )
    return t, agents


# Initial build
_config = get_config()
team, _agents = _build_team(_config)


def reload_team():
    """Reload the team from the current config on disk.

    Called by the dashboard's /agents/api/reload endpoint.
    """
    global team, _agents, _config
    _config = get_config()
    team, _agents = _build_team(_config)


# ── Response helper ───────────────────────────────────────────
import re as _re


def _strip_reasoning(text: str) -> str:
    """Rimuove i tag <reasoning>...</reasoning> che Qwen3.5 inserisce nel testo."""
    return _re.sub(r"<reasoning>.*?</reasoning>", "", text, flags=_re.DOTALL).strip()


async def run_agent(user_message: str, user_id: str = "default_user") -> str:
    """Process a user message through the AI agent and return the response."""
    response = await team.arun(user_message, user_id=user_id)
    return _strip_reasoning(response.content)
