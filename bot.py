import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import os
TOKEN = os.environ.get("BOT_TOKEN")

# Guardamos alertas urgentes activas
urgent_tasks = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola.\n\n"
        "Comandos:\n"
        "/recordar <segundos> <mensaje>\n"
        "/urgente <segundos> <mensaje>"
    )

# -------- RECORDATORIO NORMAL --------
async def recordar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /recordar <segundos> <mensaje>")
        return

    segundos = int(context.args[0])
    mensaje = " ".join(context.args[1:])
    chat_id = update.effective_chat.id

    await asyncio.sleep(segundos)
    await context.bot.send_message(chat_id, f"⏰ Recordatorio:\n{mensaje}")

# -------- RECORDATORIO URGENTE --------
async def urgente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /urgente <segundos> <mensaje>")
        return

    segundos = int(context.args[0])
    mensaje = " ".join(context.args[1:])
    chat_id = update.effective_chat.id

    await update.message.reply_text("⚠️ Recordatorio urgente programado.")

    await asyncio.sleep(segundos)

    async def spam():
        while chat_id in urgent_tasks:
            await context.bot.send_message(chat_id, f"🚨 URGENTE:\n{mensaje}")
            await asyncio.sleep(3)

    task = asyncio.create_task(spam())
    urgent_tasks[chat_id] = task

# -------- DETENER URGENTE AL RESPONDER --------
async def detener_urgente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in urgent_tasks:
        urgent_tasks[chat_id].cancel()
        del urgent_tasks[chat_id]
        await update.message.reply_text("✅ Alerta urgente detenida.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("recordar", recordar))
    app.add_handler(CommandHandler("urgente", urgente))

    # Cualquier mensaje detiene alerta urgente
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detener_urgente))

    app.run_polling()

if __name__ == "__main__":
    main()
