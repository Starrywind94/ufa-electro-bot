
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

TOKEN = "8107269658:AAEPqKQX1qOBdSAoXmCsP7uDWTbIk4yD6kc"

services = {
    "Установка розетки": 520,
    "Установка автомата": 510,
    "Прокладка кабеля (м.п.)": 100,
    "Штробление (м.п.)": 340
}

STATE_SERVICE, STATE_QUANTITY = range(2)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[key] for key in services.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите услугу:", reply_markup=reply_markup)
    return STATE_SERVICE

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {"service": update.message.text}
    await update.message.reply_text("Введите количество (шт или м.п.):")
    return STATE_QUANTITY

async def quantity_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        quantity = float(update.message.text)
        service = user_data[user_id]["service"]
        price = services[service]
        total = quantity * price
        await update.message.reply_text(f"Стоимость услуги '{service}' за {quantity} = {total:.2f} ₽")
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите числовое значение.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Расчёт отменён.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, service_selected)],
            STATE_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
