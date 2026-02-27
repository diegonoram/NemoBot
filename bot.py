import os
import asyncio
import dateparser
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("BOT_TOKEN")

TIMEZONE = ZoneInfo("America/Santiago")

urgent_tasks = {}

# -------- PARSER FECHA NATURAL --------
def parse_natural(texto):
    fecha = dateparser.parse(
        texto,
        settings={
            "TIMEZONE": "America/Santiago",
            "RETURN_AS_TIMEZONE_AWARE": True,
        },
        languages=["es"]
    )
    return fecha


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola 👋\n\n"
        "Comandos disponibles:\n"
        "/recordar <fecha> | <mensaje>\n"
        "/urgente <fecha> | <mensaje>\n\n"
        "Ejemplos:\n"
        "/recordar mañana 6pm | estudiar\n"
        "/recordar en 30 minutos | sacar la ropa\n"
        "/urgente mañana 7am | despertar"
    )


# -------- RECORDATORIO NORMAL --------
async def recordar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)

    if "|" not in texto:
        await update.message.reply_text(
            "Formato correcto:\n"
            "/recordar mañana 6pm | estudiar matemáticas"
        )
        return

    parte_fecha, mensaje = texto.split("|", 1)
    fecha = parse_natural(parte_fecha.strip())

    if not fecha:
        await update.message.reply_text("No entendí la fecha.")
        return

    chat_id = update.effective_chat.id

    async def enviar(ctx):
        await ctx.bot.send_message(chat_id, f"⏰ Recordatorio:\n{mensaje.strip()}")

    context.job_queue.run_once(enviar, when=fecha)

    await update.message.reply_text("✅ Recordatorio programado.")


# -------- RECORDATORIO URGENTE --------
async def urgente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)

    if "|" not in texto:
        await update.message.reply_text(
            "Formato correcto:\n"
            "/urgente mañana 7am | despertar"
        )
        return

    parte_fecha, mensaje = texto.split("|", 1)
    fecha = parse_natural(parte_fecha.strip())

    if not fecha:
        await update.message.reply_text("No entendí la fecha.")
        return

    chat_id = update.effective_chat.id

    async def activar_urgente(ctx):
        async def spam():
            while chat_id in urgent_tasks:
                await ctx.bot.send_message(chat_id, f"🚨 URGENTE:\n{mensaje.strip()}")
                await asyncio.sleep(3)

        task = asyncio.create_task(spam())
        urgent_tasks[chat_id] = task

    context.job_queue.run_once(activar_urgente, when=fecha)

    await update.message.reply_text("⚠️ Recordatorio urgente programado.")


# -------- DETENER URGENTE --------
async def detener_urgente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in urgent_tasks:
        urgent_tasks[chat_id].cancel()
        del urgent_tasks[chat_id]
        await update.message.reply_text("✅ Alerta urgente detenida.")


# -------- MAIN --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("recordar", recordar))
    app.add_handler(CommandHandler("urgente", urgente))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, detener_urgente)
    )

    app.run_polling()


if __name__ == "__main__":
    main()
