import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from database import Database
from groq_solver import solve_math_problem

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Configuración ──────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "TU_TOKEN_AQUI")
FREE_DAILY_LIMIT = 3          # Consultas gratis por día
SUBSCRIPTION_PRICE = "S/. 15 al mes"

db = Database()

# ── Handlers ───────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_user(user.id, user.username or user.first_name)

    keyboard = [
        [InlineKeyboardButton("📊 Mi cuenta", callback_data="account")],
        [InlineKeyboardButton("💎 Suscribirse — " + SUBSCRIPTION_PRICE, callback_data="subscribe")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 ¡Hola, {user.first_name}!\n\n"
        "🧮 *MathBot Pro* — Tu asistente de matemáticas\n\n"
        "Puedo resolver problemas de *todos los niveles*:\n"
        "• Aritmética y fracciones\n"
        "• Álgebra y geometría\n"
        "• Cálculo y estadística\n"
        "• Y mucho más...\n\n"
        f"📩 Los usuarios *gratuitos* tienen {FREE_DAILY_LIMIT} consultas por día.\n"
        "💎 Con suscripción: consultas *ilimitadas*.\n\n"
        "✏️ Envíame tu problema matemático directamente.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    db.register_user(user_id, update.effective_user.username or update.effective_user.first_name)

    # Verificar límite
    is_premium = db.is_premium(user_id)
    if not is_premium:
        remaining = db.get_remaining_queries(user_id, FREE_DAILY_LIMIT)
        if remaining <= 0:
            keyboard = [[InlineKeyboardButton(
                "💎 Suscribirme ahora — " + SUBSCRIPTION_PRICE,
                callback_data="subscribe"
            )]]
            await update.message.reply_text(
                "⚠️ *Límite diario alcanzado*\n\n"
                f"Los usuarios gratuitos tienen {FREE_DAILY_LIMIT} consultas por día.\n"
                "¡Suscríbete para consultas ilimitadas! 🚀",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

    # Resolver problema
    thinking_msg = await update.message.reply_text("🔄 Resolviendo tu problema...")
    try:
        solution = solve_math_problem(text)
        db.increment_usage(user_id)

        if not is_premium:
            remaining = db.get_remaining_queries(user_id, FREE_DAILY_LIMIT)
            footer = f"\n\n📊 _Consultas restantes hoy: {remaining}/{FREE_DAILY_LIMIT}_"
            if remaining <= 1:
                footer += "\n💡 ¿Quieres consultas ilimitadas? /suscribir"
        else:
            footer = "\n\n💎 _Usuario Premium — Consultas ilimitadas_"

        await thinking_msg.edit_text(
            f"✅ *Solución:*\n\n{solution}{footer}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error solving: {e}")
        await thinking_msg.edit_text(
            "❌ Hubo un error al procesar tu consulta. Inténtalo de nuevo."
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "account":
        is_premium = db.is_premium(user_id)
        remaining = db.get_remaining_queries(user_id, FREE_DAILY_LIMIT)
        total = db.get_total_queries(user_id)
        status = "💎 Premium (ilimitado)" if is_premium else f"🆓 Gratuito ({remaining}/{FREE_DAILY_LIMIT} hoy)"

        await query.edit_message_text(
            f"👤 *Tu cuenta*\n\n"
            f"Estado: {status}\n"
            f"Total de consultas realizadas: {total}\n\n"
            "Usa /suscribir para obtener acceso ilimitado.",
            parse_mode="Markdown"
        )

    elif query.data == "subscribe":
        await query.edit_message_text(
            "💎 *Suscripción Premium*\n\n"
            f"Precio: *{SUBSCRIPTION_PRICE}*\n\n"
            "✅ Consultas ilimitadas\n"
            "✅ Respuestas prioritarias\n"
            "✅ Soporte dedicado\n\n"
            "📲 Para suscribirte, contáctanos:\n"
            "@tu_usuario_admin\n\n"
            "_Una vez realizado el pago, tu cuenta será activada en menos de 24 horas._",
            parse_mode="Markdown"
        )

    elif query.data == "help":
        await query.edit_message_text(
            "❓ *¿Cómo usar MathBot Pro?*\n\n"
            "Simplemente escribe tu problema matemático y te lo resuelvo paso a paso.\n\n"
            "*Ejemplos:*\n"
            "• `¿Cuánto es 15% de 340?`\n"
            "• `Resuelve: 2x² + 5x - 3 = 0`\n"
            "• `¿Cuál es la derivada de x³ + 2x?`\n"
            "• `Calcula la integral de sen(x)`\n"
            "• `¿Cuál es la probabilidad de sacar 2 ases en 5 cartas?`\n\n"
            "📌 *Comandos:*\n"
            "/start — Menú principal\n"
            "/cuenta — Ver tu cuenta\n"
            "/suscribir — Info de suscripción",
            parse_mode="Markdown"
        )


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💎 Ver planes", callback_data="subscribe")]]
    await update.message.reply_text(
        "💎 *Suscripción Premium*\n\n"
        f"Precio: *{SUBSCRIPTION_PRICE}*\n"
        "Consultas ilimitadas + soporte prioritario.\n\n"
        "Pulsa el botón para ver más detalles.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.register_user(user_id, update.effective_user.username or update.effective_user.first_name)
    is_premium = db.is_premium(user_id)
    remaining = db.get_remaining_queries(user_id, FREE_DAILY_LIMIT)
    total = db.get_total_queries(user_id)
    status = "💎 Premium (ilimitado)" if is_premium else f"🆓 Gratuito ({remaining}/{FREE_DAILY_LIMIT} hoy)"

    await update.message.reply_text(
        f"👤 *Tu cuenta*\n\n"
        f"Estado: {status}\n"
        f"Total de consultas realizadas: {total}",
        parse_mode="Markdown"
    )


# ── Admin: activar premium manualmente ────────────────────────
async def admin_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Uso: /activar <user_id>")
        return
    target_id = int(context.args[0])
    db.set_premium(target_id, True)
    await update.message.reply_text(f"✅ Usuario {target_id} activado como Premium.")


# ── Main ───────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cuenta", account_command))
    app.add_handler(CommandHandler("suscribir", subscribe_command))
    app.add_handler(CommandHandler("activar", admin_activate))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Bot iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()
