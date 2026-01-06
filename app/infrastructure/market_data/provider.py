from app.infrastructure.market_data.local_server import get_data_local
from app.infrastructure.market_data.binance_api import get_data
async def get_data_with_fallback(symbol, interval, limit):
    # Пробуем сначала локальный сервер
    local_result = await get_data_local(symbol, interval, limit)
    if local_result is not None:
        return local_result
    # Если локальный сервер не ответил — вызываем оригинальную функцию напрямую
    print(f"Локальный сервер не ответил, получаем данные с Binance API для {symbol} {interval}")
    return await get_data(symbol, interval, limit)