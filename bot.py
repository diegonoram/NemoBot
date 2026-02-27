import os
import asyncio
import dateparser
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import (
)

import os
TOKEN = os.environ.get("BOT_TOKEN")

# Guardamos alertas urgentes activas
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
        "Hola.\n\n"
        "Comandos:\n"
        "/recordar <segundos> <mensaje>\n"
        "/urgente <segundos> <mensaje>"
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
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /recordar <segundos> <mensaje>")
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

    segundos = int(context.args[0])
    mensaje = " ".join(context.args[1:])
    chat_id = update.effective_chat.id

    await update.message.reply_text("⚠️ Recordatorio programado.")
    async def enviar(ctx):
        await ctx.bot.send_message(chat_id, f"⏰ Recordatorio:\n{mensaje.strip()}")

    context.job_queue.run_once(enviar, when=fecha)

    await update.message.reply_text("✅ Recordatorio programado.")

    await asyncio.sleep(segundos)
    await context.bot.send_message(chat_id, f"⏰ Recordatorio:\n{mensaje}")

# -------- RECORDATORIO URGENTE --------
async def urgente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /urgente <segundos> <mensaje>")
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

    segundos = int(context.args[0])
    mensaje = " ".join(context.args[1:])
    chat_id = update.effective_chat.id

    await update.message.reply_text("⚠️ Recordatorio urgente programado.")
    async def activar_urgente(ctx):
        async def spam():
            while chat_id in urgent_tasks:
                await ctx.bot.send_message(chat_id, f"🚨 URGENTE:\n{mensaje.strip()}")
                await asyncio.sleep(3)

    await asyncio.sleep(segundos)
        task = asyncio.create_task(spam())
        urgent_tasks[chat_id] = task

    async def spam():
        while chat_id in urgent_tasks:
            await context.bot.send_message(chat_id, f"🚨 URGENTE:\n{mensaje}")
            await asyncio.sleep(3)
    context.job_queue.run_once(activar_urgente, when=fecha)

    await update.message.reply_text("⚠️ Recordatorio urgente programado.")

    task = asyncio.create_task(spam())
    urgent_tasks[chat_id] = task

# -------- DETENER URGENTE AL RESPONDER --------
# -------- DETENER URGENTE --------
async def detener_urgente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

@@ -68,17 +115,21 @@ async def detener_urgente(update: Update, context: ContextTypes.DEFAULT_TYPE):
        del urgent_tasks[chat_id]
        await update.message.reply_text("✅ Alerta urgente detenida.")


# -------- MAIN --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("recordar", recordar))
    app.add_handler(CommandHandler("urgente", urgente))

    # Cualquier mensaje detiene alerta urgente
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detener_urgente))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, detener_urgente)
    )

    app.run_polling()


if __name__ == "__main__":
    main()
