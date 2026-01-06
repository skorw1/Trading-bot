from app.infrastructure.config import get_or_ask
from aiogram import Bot
bot = None

ALLOWED_USER_ID = get_or_ask('telegram_user_id', 'Введіть id телеграм користувача: ')

def init_token(token: str):
    global bot
    bot = Bot(token=token)

TOKEN = get_or_ask('telegram_token', 'Введіть токен телеграм бота: ')
bot = init_token(TOKEN)