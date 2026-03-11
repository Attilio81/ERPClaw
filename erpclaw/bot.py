"""Telegram bot that forwards messages to the AI agent."""

import logging
import tempfile

from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from erpclaw.agent import run_agent
from erpclaw.config import ALLOWED_CHAT_ID, OPENAI_API_KEY, TELEGRAM_BOT_TOKEN

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _is_allowed(update: Update) -> bool:
    """Return True only if the sender matches the configured ALLOWED_CHAT_ID."""
    return str(update.effective_user.id) == ALLOWED_CHAT_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    if not _is_allowed(update):
        return
    await update.message.reply_text(
        "👋 Ciao! Sono *ERPClaw*, il tuo gestionale aziendale controllato via chat.\n\n"
        "Puoi scrivermi in linguaggio naturale (o mandarmi un *messaggio vocale*) per:\n\n"
        "📦 *Articoli & Categorie*\n"
        "• Creare, cercare e modificare articoli\n"
        "• Gestire categorie e scorte minime\n\n"
        "🏭 *Magazzino*\n"
        "• Assegnare stock alle ubicazioni\n"
        "• Trasferire merce tra scaffali\n"
        "• Scaricare ordini spediti\n\n"
        "🛒 *Ordini & Clienti*\n"
        "• Creare e gestire ordini\n"
        "• Aggiungere clienti e indirizzi\n"
        "• Seguire il ciclo bozza → confermato → spedito → chiuso\n\n"
        "🔍 *Fornitori*\n"
        "• Ricercare fornitori sul web\n"
        "• Scaricare e analizzare cataloghi PDF\n\n"
        "Scrivi pure quello che ti serve, per esempio:\n"
        "_\"crea un articolo Vite M6 a 0,05€\"_\n"
        "_\"quante unità di Vite M6 ho in magazzino?\"_\n"
        "_\"lista articoli sotto scorta minima\"_",
        parse_mode="Markdown",
    )


MAX_MSG_LEN = 4096


def _split_message(text: str, max_len: int = MAX_MSG_LEN) -> list[str]:
    """Split text into chunks of at most max_len characters, breaking on newlines where possible."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


async def _reply(update: Update, response: str) -> None:
    """Send response, splitting into multiple messages if needed."""
    chunks = _split_message(response)
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(chunk)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward every text message to the AI agent and reply with the result."""
    if not _is_allowed(update):
        return
    user_text = update.message.text
    logger.info("Message from %s: %s", update.effective_user.username, user_text)

    response = await run_agent(user_text, user_id=str(update.effective_user.id))
    await _reply(update, response)


async def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio file using OpenAI Whisper."""
    with open(file_path, "rb") as audio_file:
        transcription = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
    return transcription.text


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download a voice/audio message, transcribe it, and forward to the agent."""
    if not _is_allowed(update):
        return
    voice = update.message.voice or update.message.audio
    file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        tmp_path = tmp.name

    logger.info("Voice message from %s, transcribing…", update.effective_user.username)
    transcript = await transcribe_audio(tmp_path)
    logger.info("Transcript: %s", transcript)

    await update.message.reply_text(f"🎤 Trascrizione: {transcript}")

    response = await run_agent(transcript, user_id=str(update.effective_user.id))
    await _reply(update, response)


def create_app() -> Application:
    """Build and return the Telegram Application (bot)."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    return app


def main() -> None:
    """Entry point — start polling for updates."""
    app = create_app()
    logger.info("Bot started, polling…")
    app.run_polling()
