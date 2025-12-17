import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from groq import Groq

# ==== Config via variáveis de ambiente (definidas no Render) ====
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

WEBHOOK_PATH = "/webhook"
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")  # setado pelo Render em runtime

# Cliente Groq
groq_client = Groq(api_key=GROQ_API_KEY)

# ==== Telegram Application ====
application = (
    Application.builder()
    .token(TELEGRAM_TOKEN)
    .build()
)

# ==== Handlers ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Sou um bot com IA Groq. Envie uma mensagem e responderei com o modelo Llama3."
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # Chamada à Groq API (Responses / Chat Completions)
    completion = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Você é um assistente jurídico/técnico útil, responda em português do Brasil."
            },
            {
                "role": "user",
                "content": user_text,
            },
        ],
        temperature=0.3,
    )

    answer = completion.choices[0].message.content
    await update.message.reply_text(answer)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# ==== FastAPI + ciclo de vida (para webhook funcionar no Render) ====
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa bot ptb
    await application.initialize()

    # Se o Render já expôs a URL externa, configura webhook automaticamente
    if RENDER_EXTERNAL_URL:
        webhook_url = RENDER_EXTERNAL_URL + WEBHOOK_PATH
        await application.bot.set_webhook(webhook_url)

    await application.start()
    yield
    await application.stop()
    await application.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}
