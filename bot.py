import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.environ["BOT_TOKEN"]  # defina BOT_TOKEN no Render
WEBHOOK_PATH = "/webhook"        # mesma rota que você usará no setWebhook

# cria aplicação do python-telegram-bot
application = (
    Application.builder()
    .token(TOKEN)
    .build()
)

# ====== HANDLERS DO SEU BOT ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot online no Render!")

application.add_handler(CommandHandler("start", start))
# aqui você adiciona os demais handlers que já tinha no seu código
# application.add_handler(...)

# ====== FASTAPI + LIFESPAN PARA CONFIGURAR WEBHOOK ======
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render preenche em runtime


@asynccontextmanager
async def lifespan(app: FastAPI):
    # só tenta setar webhook se tiver URL externa disponível
    if RENDER_EXTERNAL_URL:
        webhook_url = RENDER_EXTERNAL_URL + WEBHOOK_PATH
        await application.bot.set_webhook(webhook_url)
    await application.initialize()
    await application.start()
    yield
    await application.stop()
    await application.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    """Endpoint chamado pelo Telegram."""
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


@app.get("/health")
async def health():
    """Usado pelo Render para health check."""
    return {"status": "ok"}
