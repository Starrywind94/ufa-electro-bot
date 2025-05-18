
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from fpdf import FPDF
from io import BytesIO

TOKEN = "8107269658:AAEPqKQX1qOBdSAoXmCsP7uDWTbIk4yD6kc"

services = {
    "Установка розетки (шт)": 520,
    "Установка автомата (шт)": 510,
    "Прокладка кабеля (м.п.)": 100,
    "Штробление (м.п.)": 340
}

STATE_SERVICE, STATE_QUANTITY = range(2)
user_cart = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[key] for key in services.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Выберите услугу (или введите /done для завершения):", reply_markup=reply_markup)
    return STATE_SERVICE

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    service = update.message.text
    if service not in services:
        await update.message.reply_text("Пожалуйста, выберите услугу из списка.")
        return STATE_SERVICE
    context.user_data["current_service"] = service
    await update.message.reply_text(f"Введите количество для '{service}':")
    return STATE_QUANTITY

async def quantity_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        quantity = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите числовое значение.")
        return STATE_QUANTITY

    service = context.user_data["current_service"]
    if user_id not in user_cart:
        user_cart[user_id] = []
    user_cart[user_id].append((service, quantity, services[service]))

    await update.message.reply_text("Добавлено! Чтобы завершить — /done. Чтобы добавить ещё — выберите следующую услугу.")
    return STATE_SERVICE

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_cart or not user_cart[user_id]:
        await update.message.reply_text("Ваша корзина пуста.")
        return ConversationHandler.END

    total = 0
    text_lines = ["Ваша смета:\n"]
    for service, qty, price in user_cart[user_id]:
        line_total = qty * price
        total += line_total
        text_lines.append(f"• {service} — {qty} × {price} ₽ = {line_total:.2f} ₽")
    text_lines.append(f"\nИТОГО: {total:.2f} ₽")
    full_text = "\n".join(text_lines)

    await update.message.reply_text(full_text)

    # Генерация PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Смета по электромонтажным работам", ln=True, align="C")
    pdf.ln(10)
    for line in text_lines:
        pdf.multi_cell(0, 10, line)

    pdf_stream = BytesIO()
    pdf.output(pdf_stream)
    pdf_stream.seek(0)
    await update.message.reply_document(InputFile(pdf_stream, filename="smeta.pdf"))

    user_cart[user_id] = []
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
        fallbacks=[
            CommandHandler("done", done),
            CommandHandler("cancel", cancel)
        ]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
