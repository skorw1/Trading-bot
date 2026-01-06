from decimal import Decimal, ROUND_DOWN
from math import floor
def round_to_tick_size(price, tick_size):
    try:
        # Преобразуем цену и tick_size в тип Decimal для точных вычислений
        price = Decimal(str(price))
        tick_size = Decimal(str(tick_size))

        # Рассчитываем количество знаков после запятой для tick_size
        tick_size_str = f"{tick_size:.20f}".rstrip('0')
        decimal_places = len(tick_size_str.split('.')[1]) if '.' in tick_size_str else 0
        print(f"tick size: {tick_size}, decimal places: {decimal_places}")

        # Вычисляем округленную цену с учетом точности
        rounded_price = (price // tick_size) * tick_size

        # Округляем до нужной точности
        rounded_price = rounded_price.quantize(Decimal(f'1e-{decimal_places}'), rounding=ROUND_DOWN)
        print(f"rounded price: {rounded_price}")

        return float(rounded_price)
    except Exception as e:
        print(f"Ошибка в функции round_to_tick_size: {e}")
        return None

def round_to_step_size(quantity, step_size):
    return round(floor(quantity / step_size) * step_size, len(str(step_size).split('.')[1]))