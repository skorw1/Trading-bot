from binance import AsyncClient
from app.infrastructure.config import get_or_ask

API_KEY = get_or_ask('binance_api_key', 'Введіть API KEY Binance: ')
SECRET_KEY = get_or_ask('binance_secret_key', 'Введіть SECRET KEY Binance: ')


async def create_client(api_key, secret_key):
    """
    Создаёт глобальный экземпляр клиента Binance.
    """

    return await AsyncClient.create(api_key, secret_key)


client = create_client(API_KEY, SECRET_KEY)

async def close_client():
    """
    Закрывает глобальный экземпляр клиента Binance, если он существует.
    """
    global client
    if client is not None:
        await client.close_connection()
        client = None
        print("Клиент Binance закрыт.")
    else:
        print("Клиент Binance уже был закрыт.")