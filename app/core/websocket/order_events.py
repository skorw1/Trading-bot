from app.core.trading.state import tracking_orders, tracking_orders_for_limit
from app.infrastructure.market_data.binance_api import get_step_size
from app.core.calculations.precising import round_to_step_size, round_to_tick_size
from app.infrastructure.telegram import ALLOWED_USER_ID, bot
from app.core.trading.trade_flow import close_all_orders_and_positions
async def handle_socket_messages(msg, client):
    """
    Обрабатывает сообщения из WebSocket.
    """
    print(msg)
    if msg['e'] == 'ORDER_TRADE_UPDATE':  # Событие об ордере
        msg = msg['o']
        order_status = msg['X']  # Статус ордера (например, FILLED)
        order_type = msg['ot']    # Тип ордера (например, TAKE_PROFIT_MARKET)
        executed_qty = msg['l']  # Исполненное количество
        executed_price = msg['L']  # Цена исполнения
        symbol = msg['s']
        order_id = msg['i']  # ID ордера

        if order_status == 'FILLED' and order_type == 'LIMIT':
            # Если это лимитный ордер, проверяем в tracking_orders
            if order_id in tracking_orders:
                tracking_data = tracking_orders[order_id]
                market_order_price = tracking_data['market_order_price']
                market_quantity = tracking_data['market_quantity']
                limit_order_price = tracking_data['limit_order_price']
                limit_quantity = tracking_data['limit_quantity']
                take_profit1 = tracking_data['take_profit1']
                take_profit_side = tracking_data['take_profit_side']
                tick_size = tracking_data['tick_size']
                take_profit_id = tracking_data['take_profit_id']
                step_size = await get_step_size(symbol, client)
                stop_loss_id = tracking_data['stop_loss_id']
                print(tracking_orders[order_id])
                print(f"Лимитный ордер исполнен для {symbol}: Цена {executed_price}, Количество {executed_qty}")
                # Создание ордера тейк-профита
                average_price = (market_order_price * market_quantity + limit_order_price * limit_quantity) / (market_quantity + limit_quantity)
                if take_profit_side == 'BUY':
                    tp_price = round_to_tick_size(average_price * (1-take_profit1/100), tick_size)
                elif take_profit_side == 'SELL':
                    tp_price = round_to_tick_size(average_price * (1+take_profit1/100), tick_size)
                print(f"Тейк-профит на цену {tp_price}")
                try:
                    await client.futures_cancel_order(symbol=symbol, orderId=take_profit_id)
                    del tracking_orders[take_profit_id]
                    del tracking_orders[stop_loss_id]

                    print('limit tracking orders:', tracking_orders)
                    print('логика1 новой лимитки', symbol, take_profit_side, tp_price, limit_quantity+market_quantity)
                    quantity_total = round_to_step_size(limit_quantity+market_quantity, step_size)
                    order_tp_data = await client.futures_create_order(
                        symbol=symbol,
                        side=take_profit_side,  # Используем сторону тейк-профита
                        type='TAKE_PROFIT_MARKET',
                        stopPrice=tp_price,
                        quantity=quantity_total,
                        timeInForce='GTC'
                    )
                    tracking_orders_for_limit[order_tp_data['orderId']] = {
                        'stop_loss_id': stop_loss_id
                    }
                    print(f"Тейк-профит установлен на уровне {tp_price}")
                except Exception as e:
                    print(f"Ошибка при установке тейк-профита: {e}")
                    try:
                        await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Помилка: {e} при виставлені лімітного ордеру для {symbol}, зі стороною {take_profit_side}, по ціні {tp_price}, та з кількістью {quantity_total}')
                    except Exception as e:
                        print('Exception on await send message:', e)
                # Удаляем лимитный ордер из tracking_orders после исполнения
                del tracking_orders[order_id]
            else:
                print('Лимитный ордер выполнен, но его нету в tracking_orders')
        elif order_status == 'FILLED' and order_type == 'TAKE_PROFIT_MARKET':
            try:
                if order_id in tracking_orders:
                    print('Вывожу информацию про весь tracking_orders:')
                    tracking_data = tracking_orders[order_id]
                    market_order_price = tracking_data['market_order_price']
                    market_quantity = tracking_data['market_quantity']
                    limit_order_price = tracking_data['limit_order_price']
                    limit_quantity = tracking_data['limit_quantity']
                    take_profit1 = tracking_data['take_profit1']
                    take_profit_side = tracking_data['take_profit_side']
                    take_profit_quantity1 = tracking_data['take_profit_quantity1']
                    take_profit_quantity2 = tracking_data['take_profit_quantity2']
                    take_profit_quantity3 = tracking_data['take_profit_quantity3']
                    tick_size = tracking_data['tick_size']
                    take_profit_id = tracking_data['take_profit_id']
                    step_size = await get_step_size(symbol, client)
                    counter = tracking_data['counter']
                    take_profit_price1 = tracking_data['take_profit_price1']
                    take_profit_price2 = tracking_data['take_profit_price2']
                    take_profit_price3 = tracking_data['take_profit_price3']
                    stop_loss_id = tracking_data['stop_loss_id']
                    print('counter:', counter, str(tracking_data))
                    if counter == 1:
                        print('inside counter 1')
                        new_take_profit = await client.futures_create_order(
                            symbol=symbol,
                            side=take_profit_side,  # Используем сторону тейк-профита
                            type='TAKE_PROFIT_MARKET',
                            stopPrice=take_profit_price2,
                            quantity=take_profit_quantity2,
                            timeInForce='GTC'
                        )
                        print('после тейк профит 2 выставления:', new_take_profit)
                        res = await client.futures_cancel_order(symbol=symbol, orderId=stop_loss_id)
                        print('после отмены стопа:', res)
                        sl = await client.futures_create_order(
                            symbol=symbol,
                            side=take_profit_side,
                            type='STOP_MARKET',
                            stopPrice=market_order_price,
                            quantity=take_profit_quantity1
                        )
                        print('выставлен новый стоп', sl)
                        tracking_orders[new_take_profit['orderId']] = tracking_orders[order_id].copy()
                        print('после копирования в tracking orders нового тейка')
                        tracking_orders[new_take_profit['orderId']]['stop_loss_id'] = sl['orderId']
                        print('после присвоения нового стоп лосса для предыдущего тейка в tracking orders')
                        tracking_orders[sl['orderId']] = {
                            'take_profit_id': order_id
                        }
                        print('после создания новой записи в tracking для стопа')
                        tracking_orders[new_take_profit['orderId']]['counter'] += 1
                        print('После увеличения counter:', tracking_orders[new_take_profit['orderId']]['counter'])

                        del tracking_orders[order_id]
                        print(f'перед удалением стопа с id {stop_loss_id} из tracking orders:', tracking_orders)
                        del tracking_orders[stop_loss_id]
                        print('после удаления стопа из tracking orders')
                        try:
                            await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Виконався тейк профіт для {symbol}. Встановлено новий тейк на 30%, і стоп лосс"')
                        except Exception as e:
                            print(f'Exception on await send message: {e}')
                    elif counter == 2:
                        print('inside counter 2')
                        new_take_profit = await client.futures_create_order(
                            symbol=symbol,
                            side=take_profit_side,  # Используем сторону тейк-профита
                            type='TAKE_PROFIT_MARKET',
                            stopPrice=take_profit_price3,
                            quantity=take_profit_quantity3,
                            timeInForce='GTC'
                        )
                        await client.futures_cancel_order(symbol=symbol, orderId=stop_loss_id)
                        sl = await client.futures_create_order(
                            symbol=symbol,
                            side=take_profit_side,
                            type='STOP_MARKET',
                            stopPrice=take_profit_price1,
                            quantity=take_profit_quantity3
                        )
                        tracking_orders[new_take_profit['orderId']] = tracking_orders[order_id]
                        tracking_orders[new_take_profit['orderId']]['stop_loss_id'] = sl['orderId']
                        tracking_orders[sl['orderId']] = {
                            'take_profit_id': order_id
                        }
                        tracking_orders[new_take_profit['orderId']]['counter'] += 1
                        print('После увеличения counter:', tracking_orders[new_take_profit['orderId']]['counter'])
                        del tracking_orders[order_id] # Удаляем из отслеживания уже исполнившиеся ордера
                        del tracking_orders[stop_loss_id] # Удаляем из отслеживания уже исполнившиеся ордера
                        try:
                            await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Виконався тейк профіт для {symbol}. Встановлено новий тейк на 20%, і стоп лосс"')
                        except Exception as e:
                            print(f'Exception on await send message: {e}')
                    elif counter == 3:
                        await close_all_orders_and_positions(symbol) # закрываем все позиции и ордера после выполнения третьего тейка
                        del tracking_orders[order_id]
                        del tracking_orders[stop_loss_id]
                        try:
                            await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Виконався тейк профіт для {symbol}. Видалені усі ордери по торговій парі."')
                        except Exception as e:
                            print(f'Exception on await send message: {e}')
                    else:
                        print('error in counter!!!')
                elif order_id in tracking_orders_for_limit:
                    data = tracking_orders_for_limit[order_id]

                    stop_loss_id = data['stop_loss_id']
                    try:
                        await client.futures_cancel_order(symbol=symbol, orderId=stop_loss_id)
                        try:
                            await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Успішно видалено стоп-лосс ордер після виконання тейк профіту (ліміт усереднення)')
                        except Exception as ex:
                            print(f'Exception on await send message: {ex}')
                    except Exception as e:
                        await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Помилка при видаленні стоп лоссу після виконання тейк профіт ордеру (ліміт усереднення): {e}')
                    del tracking_orders_for_limit[order_id]
                else:
                    print(f'order id {order_id} does not exist in any tracking orders id.')
            except Exception as e:
                print('Exception', e)
                try:
                    await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Виконався стоп лосс для {symbol}. Видалено усі ордери по торговій парі"')
                except Exception as exep:
                    print(f'Exception on await send message: {exep}')
        elif order_status == 'FILLED' and order_type == 'STOP_MARKET':
            print(f"{order_type} исполнен для {symbol}: Количество {executed_qty}, Цена {executed_price}")
            await close_all_orders_and_positions(symbol)
            take_profit_id = tracking_orders[order_id]['take_profit_id']
            del tracking_orders[order_id]
            del tracking_orders[take_profit_id]
            try:
                await bot.send_message(chat_id=ALLOWED_USER_ID, text=f'Виконався стоп лосс для {symbol}. Видалено усі ордери по торговій парі"')
            except Exception as e:
                print(f'Exception on await send message: {e}')