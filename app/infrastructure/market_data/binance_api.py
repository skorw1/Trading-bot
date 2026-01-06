from binance import AsyncClient
import aiohttp
async def get_current_position_quantity(symbol, client):
    positions = await client.futures_account()
    for position in positions['positions']:
        if position['symbol'] == symbol:
            return abs(float(position['positionAmt']))  # Возвращаем абсолютное количество

async def get_tick_size(symbol, client):

    info = await client.futures_exchange_info()
    symbols = info.get('symbols', [])
    # Проверяем, есть ли символ в списке
    for s in symbols:
        if s.get('symbol') == symbol:
            filters = s.get('filters', [])
            if not filters or len(filters) < 1:
                print(f"Отсутствуют фильтры для символа {symbol}. Полные данные: {s}")
                return None
            tick_size = filters[0].get('tickSize')
            if tick_size is None:
                print(f"Ключ 'tickSize' отсутствует в фильтре: {filters[0]}")
                return None
            # Преобразуем tick_size из научной нотации в float и проверяем точность
            tick_size = float(f"{float(tick_size):.10g}")  # Ограничиваем до 10 значащих цифр
            print(f"Tick size для {symbol}: {tick_size}")
            return tick_size
    # Если символ не найден
    print(f"Символ {symbol} не найден в данных биржи. Ответ Binance: {info}")
    return None


async def get_current_price(symbol, client: AsyncClient):
    ticker = await client.futures_symbol_ticker(symbol=symbol)
    print(ticker)
    return float(ticker['price'])


async def get_step_size(symbol, client):
    info = await client.futures_exchange_info()
    for s in info['symbols']:
        if s['symbol'] == symbol:
            return float(s['filters'][2]['stepSize'])

async def get_open_orders_by_pair(client: AsyncClient, symbol: str):
    try:
        # Получение всех открытых ордеров для указанной валютной пары
        open_orders = await client.futures_get_open_orders(symbol=symbol)
        return open_orders
    except Exception as e:
        print(f"Ошибка при получении открытых ордеров: {e}")
        return []

async def get_data(symbol, interval, limit):
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    # Проверяем на наличие ошибок в ответе
    if isinstance(data, dict) and "code" in data:
        raise ValueError(f"Ошибка API Binance: {data}")

    # Проверяем корректность формата данных
    if not data or not all(isinstance(row, list) and len(row) >= 5 for row in data):
        raise ValueError("Некорректный формат данных, полученных от API")

    # Извлекаем необходимые данные
    open_prices = [float(each[1]) for each in data]  # Открытие
    high_prices = [float(each[2]) for each in data]  # Высокий
    low_prices = [float(each[3]) for each in data]   # Низкий
    close_prices = [float(each[4]) for each in data] # Закрытие

    # Логируем первые 5 значений для диагностики

    return open_prices, high_prices, low_prices, close_prices