from app.infrastructure.config import get_or_ask
from aiogram import Bot
bot = None

def init_token(token: str):
    global bot
    bot = Bot(token=token)

async def safe_answer(message, text: str) -> None:
    try:
        await message.answer(text)
    except Exception:
        print("Failed to send message")

ALLOWED_USER_ID = get_or_ask('telegram_user_id', 'Введіть id телеграм користувача: ')

TOKEN = get_or_ask('telegram_token', 'Введіть токен телеграм бота: ')
bot = init_token(TOKEN)