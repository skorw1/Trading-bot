
from app.infrastructure.market_data.binance_api import get_step_size, get_current_price
from app.core.calculations.precising import round_to_step_size
async def calculate_qn(dep, leverage, symb, client):
    step_size = await get_step_size(symb, client)  # Получаем stepSize для символа
    current_price = await get_current_price(symb, client)
    usdt_amount = dep * leverage
    quantity = usdt_amount / current_price
    rounded_quantity = round_to_step_size(quantity, step_size)  # Округляем количество
    print(f"Количество для {symb}: {rounded_quantity}")
    print(rounded_quantity)
    return rounded_quantity, current_price

async def calculate_limit_qn(dep, limit_x, limit_percent, symb, client):
    step_size = await get_step_size(symb, client)  # Получаем stepSize для символа
    current_price = await get_current_price(symb, client)
    current_price = current_price / 100 * (100-limit_percent)
    usdt_amount = dep * limit_x
    quantity = usdt_amount / current_price
    rounded_quantity = round_to_step_size(quantity, step_size)  # Округляем количество
    print(f"Количество для {symb}: {rounded_quantity}")
    print(rounded_quantity)
    return rounded_quantity