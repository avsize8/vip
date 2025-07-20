import os
import asyncio
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
import logging
from datetime import datetime, timedelta

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Проверка токена
if not TOKEN:
    raise ValueError("Не указан TELEGRAM_BOT_TOKEN в .env файле!")
if not ADMIN_CHAT_ID:
    raise ValueError("Не указан TELEGRAM_CHAT_ID в .env файле!")

logger.info(f"Бот запускается с токеном: {TOKEN[:5]}...")

class TelegramBotHelper:
    """Класс для работы с Telegram ботом"""
    
    def __init__(self):
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        if str(update.effective_chat.id) != ADMIN_CHAT_ID:
            await update.message.reply_text('Доступ запрещен')
            return
        
        keyboard = [
            [InlineKeyboardButton("📋 Новые заявки", callback_data='new')],
            [InlineKeyboardButton("📊 Все заявки", callback_data='all')],
            [InlineKeyboardButton("📈 Статистика", callback_data='stats')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            '🤖 Панель управления заявками\nВыберите действие:',
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        if str(update.effective_chat.id) != ADMIN_CHAT_ID:
            await update.message.reply_text('Доступ запрещен')
            return
        
        help_text = """
🤖 <b>Команды бота:</b>

/start - Главное меню
/help - Справка
/stats - Статистика заявок
/new - Новые заявки
/all - Все заявки

📝 <b>Функции:</b>
• Просмотр новых заявок
• Отметка заявок как обработанные
• Просмотр статистики
• Управление через кнопки
        """
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /stats"""
        if str(update.effective_chat.id) != ADMIN_CHAT_ID:
            await update.message.reply_text('Доступ запрещен')
            return
        
        try:
            from app import create_app
            from app.models import get_application_stats
            
            app = create_app()
            with app.app_context():
                stats = get_application_stats()
                
                stats_text = f"""
📊 <b>Статистика заявок:</b>

📋 Всего заявок: {stats['total']}
🆕 Новых: {stats['new']}
✅ Обработанных: {stats['processed']}
⏳ В работе: {stats['pending']}

📅 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}
                """
                await update.message.reply_text(stats_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await update.message.reply_text('❌ Ошибка при получении статистики')
    
    async def list_applications(self, update: Update, context: ContextTypes.DEFAULT_TYPE, status=None) -> None:
        """Список заявок"""
        query = update.callback_query
        await query.answer()
        
        try:
            from app import create_app
            from app.models import Application
            
            app = create_app()
            with app.app_context():
                if status:
                    applications = Application.query.filter_by(status=status).order_by(Application.created_at.desc()).limit(10).all()
                else:
                    applications = Application.query.order_by(Application.created_at.desc()).limit(10).all()
                
                if not applications:
                    await query.edit_message_text('📭 Нет заявок')
                    return
                
                for app_item in applications:
                    message = self.format_application_message(app_item)
                    
                    keyboard = []
                    if app_item.status == 'new':
                        keyboard.append([InlineKeyboardButton("✅ Обработать", callback_data=f'processed_{app_item.id}')])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=message,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                
                status_text = f"📋 {'Новые' if status == 'new' else 'Все'} заявки: {len(applications)}"
                await query.edit_message_text(status_text)
                
        except Exception as e:
            logger.error(f"Error listing applications: {e}")
            await query.edit_message_text('❌ Ошибка при получении заявок')
    
    def format_application_message(self, application):
        """Форматирование сообщения о заявке"""
        status_emoji = "🆕" if application.status == 'new' else "✅"
        status_text = "Новая" if application.status == 'new' else "Обработана"
        
        return f"""
<b>{status_emoji} Заявка #{application.id}</b>
━━━━━━━━━━━━━━
📝 <b>Имя:</b> {application.name}
📞 <b>Телефон:</b> {application.phone}
📧 <b>Email:</b> {application.email or 'Не указан'}
🛠 <b>Услуга:</b> {application.service_type or 'Не указана'}
📋 <b>Сообщение:</b> {application.message or 'Не указано'}
━━━━━━━━━━━━━━
📅 <b>Дата:</b> {application.created_at.strftime('%d.%m.%Y %H:%M')}
🆔 <b>Статус:</b> {status_text}
        """
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик кнопок"""
        query = update.callback_query
        data = query.data
        
        try:
            if data.startswith('processed_'):
                app_id = data.split('_')[1]
                await self.process_application(query, app_id)
            elif data == 'new':
                await self.list_applications(update, context, status='new')
            elif data == 'all':
                await self.list_applications(update, context)
            elif data == 'stats':
                await self.stats_command(update, context)
        except Exception as e:
            logger.error(f"Error in button handler: {e}")
            await query.answer('❌ Произошла ошибка')
    
    async def process_application(self, query, app_id):
        """Обработка заявки"""
        try:
            from app import create_app
            from app.models import Application, db
            
            app = create_app()
            with app.app_context():
                application = Application.query.get(app_id)
                if application:
                    application.status = 'processed'
                    db.session.commit()
                    await query.answer('✅ Заявка отмечена как обработанная')
                    await query.edit_message_reply_markup(reply_markup=None)
                else:
                    await query.answer('❌ Заявка не найдена')
        except Exception as e:
            logger.error(f"Error processing application: {e}")
            await query.answer('❌ Ошибка при обработке')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений"""
        if str(update.effective_chat.id) != ADMIN_CHAT_ID:
            await update.message.reply_text('Доступ запрещен')
            return
        
        await update.message.reply_text(
            'Используйте команду /start для управления заявками или /help для справки'
        )
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def run(self):
        """Запуск бота"""
        try:
            self.application = Application.builder().token(TOKEN).build()
            self.setup_handlers()
            
            logger.info("Бот успешно запущен!")
            self.application.run_polling()
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")

def main() -> None:
    """Главная функция"""
    bot = TelegramBotHelper()
    bot.run()

if __name__ == '__main__':
    main()