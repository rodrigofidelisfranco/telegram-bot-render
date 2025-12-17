
import os
import logging
from dotenv import load_dotenv

from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from langchain_groq import ChatGroq

# 1. Carregar variáveis de ambiente (Segurança)
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Verificação básica para não rodar sem chaves
if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise ValueError("ERRO: As chaves TELEGRAM_TOKEN ou GROQ_API_KEY não foram encontradas no arquivo .env")

# 2. Configuração de Logs (Para você ver o que acontece no terminal)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 3. Configurar o Modelo IA (LangChain)
# Aumentei max_tokens para respostas mais completas se necessário
chat = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant", 
    temperature=0.5,  # Um pouco mais criativo, mas ainda focado
    max_tokens=512
)

# --- FUNÇÕES DO BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem de boas-vindas quando o comando /start é acionado."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Olá, {user_name}! Sou seu assistente virtual inteligente.\n"
        "Pode me perguntar qualquer coisa que tentarei ajudar."
    )

async def responder_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recebe a mensagem do usuário, envia para a Groq e responde."""
    user_message = update.message.text
    
    # Log no terminal (ajuda a debugar)
    logger.info(f"Mensagem recebida de {update.effective_user.first_name}: {user_message}")

    try:
        # 4. UX: Mostrar que o bot está "escrevendo" enquanto a IA pensa
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

        # 5. Processamento Assíncrono (ainvoke)
        # Usamos ainvoke em vez de invoke para não travar o bot
        messages = [
            ("system", "Você é um assistente útil, direto e educado."),
            ("human", user_message),
        ]
        
        # Chama a IA
        resposta_ia = await chat.ainvoke(messages)
        
        # Envia a resposta de volta para o Telegram
        await update.message.reply_text(resposta_ia.content)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        await update.message.reply_text("Desculpe, tive um erro interno ao processar sua solicitação. Tente novamente.")

def main() -> None:
    """Inicia o bot."""
    # Criar a aplicação
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Adicionar os manipuladores (Handlers)
    application.add_handler(CommandHandler("start", start))
    
    # O filtro filters.TEXT & ~filters.COMMAND garante que ele só leia textos que não são comandos
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensagem))

    # Iniciar o bot
    print(f"Bot iniciado com sucesso! Aguardando mensagens...")
    application.run_polling()

if __name__ == "__main__":
    main()
