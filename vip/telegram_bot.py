import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DB_PATH = 'instance/applications.db'

# Проверка токена
if not TOKEN:
    raise ValueError("Не указан TELEGRAM_BOT_TOKEN в .env файле!")
if not ADMIN_CHAT_ID:
    raise ValueError("Не указан TELEGRAM_CHAT_ID в .env файле!")

print(f"Бот запускается с токеном: {TOKEN[:5]}...")  # Логируем первые 5 символов токена

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text('Доступ запрещен')
        return
    
    keyboard = [
        [InlineKeyboardButton("Новые заявки", callback_data='new')],
        [InlineKeyboardButton("Все заявки", callback_data='all')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

async def list_applications(update: Update, context: ContextTypes.DEFAULT_TYPE, status=None) -> None:
    query = update.callback_query
    await query.answer()
    
    conn = get_db_connection()
    if status:
        applications = conn.execute('SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC', (status,)).fetchall()
    else:
        applications = conn.execute('SELECT * FROM applications ORDER BY created_at DESC').fetchall()
    conn.close()
    
    if not applications:
        await query.edit_message_text('Нет заявок')
        return
    
    for app in applications:
        message = f"""
<b>Заявка #{app['id']}</b>
━━━━━━━━━━━━━━
📝 <b>Имя:</b> {app['name']}
📞 <b>Телефон:</b> {app['phone']}
📧 <b>Email:</b> {app['email'] or 'Не указан'}
🛠 <b>Услуга:</b> {app['service_type'] or 'Не указана'}
📋 <b>Сообщение:</b> {app['message'] or 'Не указано'}
━━━━━━━━━━━━━━
📅 <b>Дата:</b> {app['created_at']}
🆔 <b>Статус:</b> {'Новая' if app['status'] == 'new' else 'Обработана'}
        """
        
        keyboard = []
        if app['status'] == 'new':
            keyboard.append([InlineKeyboardButton("✅ Отметить как обработанную", callback_data=f'processed_{app["id"]}')])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    await query.edit_message_text(f"Найдено заявок: {len(applications)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data
    
    if data.startswith('processed_'):
        app_id = data.split('_')[1]
        conn = get_db_connection()
        conn.execute('UPDATE applications SET status = "processed" WHERE id = ?', (app_id,))
        conn.commit()
        conn.close()
        await query.answer('✅ Заявка отмечена как обработанная')
        await query.edit_message_reply_markup(reply_markup=None)
    elif data == 'new':
        await list_applications(update, context, status='new')
    elif data == 'all':
        await list_applications(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text('Доступ запрещен')
        return
    
    await update.message.reply_text('Используйте команду /start для управления заявками')

def main() -> None:
    try:
        # Создаем Application
        application = Application.builder().token(TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота
        print("Бот успешно запущен!")
        application.run_polling()
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()