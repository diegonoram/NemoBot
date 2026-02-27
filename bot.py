import os
import re
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==============================
# CONFIG
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8000))
URL = os.getenv("RAILWAY_STATIC_URL")

TZ = ZoneInfo("America/Santiago")

# Guardamos urgentes activos
urgentes_activos = {}

# ==============================
# PARSER DE FECHA NATURAL
# ==============================

def parse_fecha(texto: str):
    ahora = datetime.now(TZ)
    texto = texto.lower().strip()

    # formato 27-02-2026 18:30
    match = re.match(r"(\d{2})-(\d{2})-(\d{4}) (\d{2}):(\d{2})", texto)
    if match:
        dia, mes, anio, hora, minuto = map(int, match.groups())
        return datetime(anio, mes, dia, hora, minuto, tzinfo=TZ)

    # mañana 18:30
    match = re.match(r"mañana (\d{2}):(\d{2})", texto)
    if match:
        hora, minuto = map(int, match.groups())
        fecha = ahora + timedelta(days=1)
        return fecha.replace(hour=hora, minute=minuto, second=0)

    # pasado mañana 18:30
    match = re.match(r"pasado mañana (\d{2}):(\d{2})", texto)
    if match:
        hora, minuto = map(int, match.groups())
        fecha = ahora + timedelta(days=2)
        return fecha.replace(hour=hora, minute=minuto, second=0)

    return None

# ==============================
# COMANDOS
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Nneemoobot activo.\n\n"
        "Comandos:\n"
        "/recordar [fecha] | mensaje\n"
        "/urgente [fecha] | mensaje\n\n"
        "Ejemplo:\n"
        "/recordar mañana 18:30 | estudiar\n"
        "/urgente 27-02-2026 18:30 | entregar tarea"
    )

# ------------------------------

async def recordar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)

    if "|" not in texto:
        await update.message.reply_text("Formato: /recordar fecha | mensaje")
        return

    fecha_txt, mensaje = map(str.strip, texto.split("|", 1))
    fecha = parse_fecha(fecha_txt)

    if not fecha:
        await update.message.reply_text("No entendí la fecha.")
        return

    delay = (fecha - datetime.now(TZ)).total_seconds()

    if delay <= 0:
        await update.message.reply_text("Esa fecha ya pasó.")
        return

    context.job_queue.run_once(
        enviar_recordatorio,
        delay,
        data={
            "chat_id": update.effective_chat.id,
            "mensaje": mensaje,
        },
    )

    await update.message.reply_text("✅ Recordatorio agendado.")

# ------------------------------

async def enviar_recordatorio(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    await context.bot.send_message(
        chat_id=data["chat_id"],
        text=f"🔔 Recordatorio: {data['mensaje']}",
    )

# ------------------------------

async def urgente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)

    if "|" not in texto:
        await update.message.reply_text("Formato: /urgente fecha | mensaje")
        return

    fecha_txt, mensaje = map(str.strip, texto.split("|", 1))
    fecha = parse_fecha(fecha_txt)

    if not fecha:
        await update.message.reply_text("No entendí la fecha.")
        return

    delay = (fecha - datetime.now(TZ)).total_seconds()

    if delay <= 0:
        await update.message.reply_text("Esa fecha ya pasó.")
        return

    context.job_queue.run_once(
        iniciar_urgente,
        delay,
        data={
            "chat_id": update.effective_chat.id,
            "mensaje": mensaje,
        },
    )

    await update.message.reply_text("🚨 Urgente agendado.")

# ------------------------------

async def iniciar_urgente(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    chat_id = data["chat_id"]
    mensaje = data["mensaje"]

    urgentes_activos[chat_id] = True

    while urgentes_activos.get(chat_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🚨 URGENTE: {mensaje}",
        )
        await asyncio.sleep(3)

# ------------------------------

async def detener_urgente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if urgentes_activos.get(chat_id):
        urgentes_activos[chat_id] = False
        await update.message.reply_text("✅ Urgente detenido.")

# ==============================
# WEBHOOK (Railway)
# ==============================

async def post_init(application):
    await application.bot.set_webhook(f"https://{URL}")

def main():
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("recordar", recordar))
    app.add_handler(CommandHandler("urgente", urgente))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detener_urgente))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"https://{URL}"
    )

if __name__ == "__main__":
    main()
