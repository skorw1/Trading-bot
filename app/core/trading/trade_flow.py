import asyncio

from app.infrastructure.time_sync import check_time
from app.core.calculations.order_calculations import calculate_qn, calculate_limit_qn
from app.core.calculations.precising import round_to_tick_size, round_to_step_size
from app.infrastructure.market_data.binance_api import get_step_size, get_tick_size

from app.infrastructure.config import ALLOWED_USER_ID
from app.infrastructure.telegram import bot, safe_send_message
from app.core.trading.state import tracking_orders
from app.infrastructure.market_data.binance_api import get_current_price, get_current_position_quantity

from binance_cl.binance_client import client

async def place_order(order_type, symbol, dep, leverage, stop_loss, take_profit1, take_profit2, take_profit3, limit_percent, limit_x, client):
    # Расчет количества актива
    await check_time(client)
    quantity, order_price = await calculate_qn(dep, leverage, symbol, client)
    step_size = await get_step_size(symbol, client)
    take_limit_quantity1 = round_to_step_size(quantity / 100 * 50, step_size)
    take_limit_quantity2 = round_to_step_size(quantity / 100 * 30, step_size)
    take_limit_quantity3 = round_to_step_size(quantity / 100 * 20, step_size)
    try:
        print('перед вычислением tick_size')
        tick_size = await get_tick_size(symbol, client)  # Получаем tickSize для символа
        print(f'после tick size, - {tick_size}')

        if order_type == 'BUY':
            # Открытие длинной позиции (лонг)
            order = await client.futures_create_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',     # Рыночный ордер
                quantity=quantity
            )
            print(order, 'Открыта лонг позиция')
            print(f'Після відкриття ордеру, прайс на пару: {order_price}')
            await asyncio.sleep(0.5)

            if take_profit1:
                try:
                    print('перед вычислением tp_price')
                    tp_price1 = round_to_tick_size(order_price * (1 + take_profit1 / 100), tick_size)
                    tp_price2 = round_to_tick_size(order_price * (1 + take_profit2 / 100), tick_size)
                    tp_price3 = round_to_tick_size(order_price * (1 + take_profit3 / 100), tick_size)
                    print(tp_price1, 'tp_price long take')
                    tp = await client.futures_create_order(
                        symbol=symbol,
                        side='SELL',      # Для лонга тейк-профит будет sell
                        type='TAKE_PROFIT_MARKET',
                        stopPrice=tp_price1,  # Рассчитанная цена тейк-профита
                        quantity=take_limit_quantity1,
                        timeInForce='GTC'
                    )
                    print(f"Тейк-профит установлен на уровне {tp_price1}")
                except Exception as e:
                    try:
                        await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Помилка при установленні тейку (лонг): "{e}"')
                    except Exception as e:
                        print(f'Exception on await send message: {e}')
                    await close_position(symbol, 'SELL', client)
                    try:
                        await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Ордер успішно закрито')
                    except Exception as e:
                        print(f'Exception on await send message: {e}')
                    return

            if stop_loss:
                print('перед вычислением sl_price')
                sl_price = round_to_tick_size(order_price * (1 - stop_loss / 100), tick_size)
                print(sl_price, 'sl_price long stop loss')
                try:
                    sl = await client.futures_create_order(
                        symbol=symbol,
                        side='SELL',      # Для лонга стоп-лосс будет sell
                        type='STOP_MARKET',
                        stopPrice=sl_price,  # Рассчитанная цена стоп-лосса
                        quantity=quantity,
                        timeInForce='GTC'
                    )
                    print(f"Стоп-лосс установлен на уровне {sl_price}")
                except Exception as e:
                    try:
                        await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Помилка при установленні стоп-лоссу (лонг): {e}')
                    except Exception as e:
                        print(f'Exception on await send message: {e}')
                    await close_position(symbol, 'SELL', client)
                    try:
                        await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Ордер успішно закрито')
                    except Exception as e:
                        print(f'Exception on await send message: {e}')
                    return

            #открытие лимит ордера
        
            try:
                # Рассчитываем цену лимитного ордера
                limit_qn = await calculate_limit_qn(dep*leverage, limit_x, limit_percent, symbol, client)
                current_price = await get_current_price(symbol, client)
                limit_price = round_to_tick_size(current_price * (1 - limit_percent / 100), tick_size)
                print(f"limig_qn: {limit_qn}, dep: {dep}, limix x: {limit_x}, limit_percent: {limit_percent}, current price: {current_price}")
                print(f"Лимитная цена для ордера: {limit_price}")
                # Создаем лимитный ордер
                limit_order = await client.futures_create_order(
                    symbol=symbol,
                    side='BUY',  # Покупка по лимитной цене
                    type='LIMIT',  # Лимитный ордер
                    price=limit_price,  # Рассчитанная цена лимитного ордера
                    quantity=limit_qn,  # Рассчитанное количество актива
                    timeInForce='GTC'  # Ордер будет активен до отмены (Good Till Cancelled)
                )
                print(f"Лимитный ордер успешно создан: {limit_order}")
                limit_order_id = limit_order['orderId']  # Получаем ID лимитного ордера
                tracking_data = {
                    'market_order_price': order_price,
                    'market_quantity': quantity,
                    'take_profit_price1': tp_price1,
                    'take_profit_price2': tp_price2,
                    'take_profit_price3': tp_price3,
                    'take_profit_quantity1': take_limit_quantity1,
                    'take_profit_quantity2': take_limit_quantity2,
                    'take_profit_quantity3': take_limit_quantity3,
                    'limit_order_price': limit_price,
                    'limit_quantity': limit_qn,
                    'take_profit1': take_profit1,
                    'take_profit2': take_profit2,
                    'take_profit3': take_profit3,
                    'tick_size': tick_size,
                    'take_profit_id': tp['orderId'],
                    'take_profit_side': 'SELL',  # Для лонга тейк-профит будет SELL
                    'stop_loss_id': sl['orderId'],
                    'counter': 1
                }
                tracking_data_for_stop = {
                    'take_profit_id': tp['orderId'],
                    'stop_loss_id': sl['orderId']
                }
                tracking_orders[limit_order_id] = tracking_data.copy()
                tracking_orders[tp['orderId']] = tracking_data.copy()
                tracking_orders[sl['orderId']] = tracking_data_for_stop
                print(f"Данные лимитного ордера добавлены в tracking_orders: {tracking_orders[limit_order_id]}")
            except Exception as e:
                print(f"Ошибка при выставлении лимитного ордера: {e}")
                try:
                    await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Ошибка при выставлении лимитного ордера: {e}')
                except Exception as e:
                    print(f'Exception on await send message: {e}')

        elif order_type == 'SELL':
            # Открытие короткой позиции (шорт)
            order = await client.futures_create_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',     # Рыночный ордер
                quantity=quantity
            )
            print(order, 'Открыта шорт позиция')

            await asyncio.sleep(0.5)

            # Получение текущей цены
            order_price = await get_current_price(symbol, client)
            print('get_current_price - корректно')

            if take_profit1:
                print('перед вычислением tp_price')
                tp_price1 = round_to_tick_size(order_price * (1 - take_profit1 / 100), tick_size)
                tp_price2 = round_to_tick_size(order_price * (1 - take_profit2 / 100), tick_size)
                tp_price3 = round_to_tick_size(order_price * (1 - take_profit3 / 100), tick_size)
                print(tp_price1, 'tp_price short take')

                try:
                    tp = await client.futures_create_order(
                        symbol=symbol,
                        side='BUY',       # Для шорта тейк-профит будет buy
                        type='TAKE_PROFIT_MARKET',
                        stopPrice=tp_price1,  # Рассчитанная цена тейк-профита
                        quantity=take_limit_quantity1,
                        timeInForce='GTC'
                    )
                    print(f"Тейк-профит установлен на уровне {tp_price1}")
                except Exception as e:
                    try:
                        await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Помилка при установленні тейку (шорт): {e}')
                    except Exception as e:
                        print(f'Exception on await send message: {e}')
                    await close_position(symbol, 'BUY', client)
                    try:
                        await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Ордер успішно закрито')
                    except Exception as e:
                        print(f'Exception on await send message: {e}')
                    return

            if stop_loss:
                print('перед вычислением sl_price')
                sl_price = round_to_tick_size(order_price * (1 + stop_loss / 100), tick_size)
                print(sl_price, 'sl_price short stop loss')
                try:
                    sl = await client.futures_create_order(
                        symbol=symbol,
                        side='BUY',       # Для шорта стоп-лосс будет buy
                        type='STOP_MARKET',
                        stopPrice=sl_price,  # Рассчитанная цена стоп-лосса
                        quantity=quantity,
                        timeInForce='GTC'
                    )
                    print(f"Стоп-лосс установлен на уровне {sl_price}")
                except Exception as e:
                    try:
                        await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Помилка при установленні стопу (шорт): {e}')
                    except Exception as e:
                        print(f'Exception on await send message: {e}')
                    await close_position(symbol, 'BUY', client)
                    try:
                        await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Ордер успішно закрито')
                    except Exception as e:
                        print(f'Exception on await send message: {e}')
                    return
            try:
                # Рассчитываем цену лимитного ордера
                limit_qn = await calculate_limit_qn(dep*leverage, limit_x, -limit_percent, symbol, client)
                current_price = await get_current_price(symbol, client)
                limit_price = round_to_tick_size(current_price * (1 + limit_percent / 100), tick_size)
                print(f"Лимитная цена для ордера: {limit_price}")
                print(f"limig_qn: {limit_qn}, dep: {dep}, limix x: {limit_x}, limit_percent: {limit_percent}, current price: {current_price}")
                print(f"Лимитная цена для ордера: {limit_price}")

                # Создаем лимитный ордер

                limit_order = await client.futures_create_order(
                    symbol=symbol,
                    side='SELL',  # Покупка по лимитной цене
                    type='LIMIT',  # Лимитный ордер
                    price=limit_price,  # Рассчитанная цена лимитного ордера
                    quantity=limit_qn,  # Рассчитанное количество актива
                    timeInForce='GTC'  # Ордер будет активен до отмены (Good Till Cancelled)
                )

                limit_order_id = limit_order['orderId']
                tracking_data = {
                    'market_order_price': order_price,
                    'market_quantity': quantity,
                    'take_profit_price1': tp_price1,
                    'take_profit_price2': tp_price2,
                    'take_profit_price3': tp_price3,
                    'take_profit_quantity1': take_limit_quantity1,
                    'take_profit_quantity2': take_limit_quantity2,
                    'take_profit_quantity3': take_limit_quantity3,
                    'limit_order_price': limit_price,
                    'limit_quantity': limit_qn,
                    'take_profit1': take_profit1,
                    'take_profit2': take_profit2,
                    'take_profit3': take_profit3,
                    'tick_size': tick_size,
                    'take_profit_id': tp['orderId'],
                    'take_profit_side': 'BUY',
                    'stop_loss_id': sl['orderId'],
                    'counter': 1
                }

                tracking_data_for_stop = {
                    'take_profit_id': tp['orderId'],
                    'stop_loss_id': sl['orderId']
                }

                tracking_orders[limit_order_id] = tracking_data.copy()
                tracking_orders[tp['orderId']] = tracking_data.copy()
                tracking_orders[sl['orderId']] = tracking_data_for_stop
            except Exception as e:
                print(f"Ошибка при выставлении лимитного ордера: {e}")
                try:
                    await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Ошибка при выставлении лимитного ордера: {e}')
                except Exception as e:
                    print(f'Exception on await send message: {e}')
        try:
            await bot.send_message(chat_id=ALLOWED_USER_ID, text=f"Успішно відкрито {'лонг' if order_type == 'BUY' else 'шорт'} позицію для {symbol}. Кількість: {quantity}. Ціна: {order_price}")
        except Exception as e:
            print(f'Exception on await send message: {e}')


    except Exception as e:
        print('Ошибка при создании ордера', e)

async def close_position(symbol, side, client):
    try:
        qty = await get_current_position_quantity(symbol, client)

        await client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=qty,
            reduceOnly=True
        )

        await safe_send_message(f"Позиция для {symbol} успешно закрыта")

    except Exception as e:
        print(f"Ошибка при закрытии позиции {symbol}: {e}")


async def cancel_all_orders(client, symbol: str):
    orders = await client.futures_get_open_orders(symbol=symbol)

    for order in orders:
        try:
            await client.futures_cancel_order(
                symbol=symbol,
                orderId=order["orderId"]
            )
            print(f"Ордер {order['orderId']} отменён")
        except Exception as e:
            print(f"Ошибка отмены ордера {order}: {e}")

async def close_all_positions(client, symbol: str):
    positions = await client.futures_position_information(symbol=symbol)

    for position in positions:
        try:
            amount = float(position.get("positionAmt", 0))
            if amount == 0:
                continue

            side = "SELL" if amount > 0 else "BUY"

            await client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=abs(amount),
                reduceOnly=True
            )

            await safe_send_message(f"Позиція для {symbol} закрита")

        except Exception as e:
            print(f"Ошибка при закрытии позиции {position}: {e}")

async def close_all_orders_and_positions(symbol: str, client):
    try:
        await cancel_all_orders(client, symbol)
        await close_all_positions(client, symbol)
    except Exception as e:
        await safe_send_message(
            f"Помилка при закритті позицій/ордерів: {e}"
        )


