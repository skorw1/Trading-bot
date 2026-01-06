from binance_cl.binance_client import client
import asyncio
from app.infrastructure.market_data.provider import get_data_with_fallback
import pandas as pd
from datetime import datetime
import ta
from app.core.trading.trade_flow import place_order
async def trade(symbol, updating, timeframe, dep, leverage, rsi_long, prev_rsi_long, rsi_short, prev_rsi_short, rsi_period, rsi_type, stop_loss, take_profit1, take_profit2, take_profit3, limit_percent, limit_x):
    position = None
    prev_rsi = None
    print(f'Запуск торговли для {symbol}. Обновление RSI происходит каждые {updating} секунд.\n')

    valid_rsi_types = {
        'open': 0,
        'high': 1,
        'low': 2,
        'close': 3,
        'hl2': 4,
        'hlc3': 5,
        'ohlc4': 6,
        'hlcc4': 7
    }

    while True:
        try:
            open_prices, high_prices, low_prices, close_prices = await get_data_with_fallback(symbol, timeframe, limit=200)

            if rsi_type not in valid_rsi_types:
                print(f"Недопустимый тип данных для RSI: {rsi_type}. Используйте один из: {', '.join(valid_rsi_types.keys())}")
                await asyncio.sleep(updating)
                break

            if rsi_type == 'open':
                rsi_data = open_prices
            elif rsi_type == 'high':
                rsi_data = high_prices
            elif rsi_type == 'low':
                rsi_data = low_prices
            elif rsi_type == 'close':
                rsi_data = close_prices
            elif rsi_type == 'hl2':
                rsi_data = [(high + low) / 2 for high, low in zip(high_prices, low_prices)]
            elif rsi_type == 'hlc3':
                rsi_data = [(high + low + close) / 3 for high, low, close in zip(high_prices, low_prices, close_prices)]
            elif rsi_type == 'ohlc4':
                rsi_data = [(open + high + low + close) / 4 for open, high, low, close in zip(open_prices, high_prices, low_prices, close_prices)]
            elif rsi_type == 'hlcc4':
                rsi_data = [(high + low + close + close) / 4 for high, low, close in zip(high_prices, low_prices, close_prices)]
            try:
                rsi_data = [float(value) for value in rsi_data]
            except ValueError as e:
                print(f"Ошибка преобразования данных в float: {e}")
                continue
            df = pd.DataFrame({rsi_type: rsi_data})
            df['rsi'] = ta.momentum.RSIIndicator(df[rsi_type], window=rsi_period).rsi()

            rsi = df['rsi'].iloc[-1]
            kiev_time = datetime.now()

            print(f'[{symbol}] RSI: {rsi}')
            if position is None:
                if prev_rsi is not None:
                    if rsi > rsi_long and prev_rsi < prev_rsi_long:
                        print(f"[{symbol}] time - {kiev_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        await place_order('BUY', symbol, dep, leverage, stop_loss, take_profit1, take_profit2, take_profit3, limit_percent, limit_x, client)
                        position = 'LONG'

                    elif rsi < rsi_short and prev_rsi > prev_rsi_short:
                        print(f"[{symbol}] RSI: {rsi}, time - {kiev_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        await place_order('SELL', symbol, dep, leverage, stop_loss, take_profit1, take_profit2, take_profit3, limit_percent, limit_x, client)
                        position = 'SHORT'

            elif position == 'LONG':
                if rsi < rsi_short and prev_rsi > prev_rsi_short:
                    print(f"[{symbol}] time - {kiev_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    await place_order('SELL', symbol, dep, leverage, stop_loss, take_profit1, take_profit2, take_profit3, limit_percent, limit_x, client)
                    position = 'SHORT'

            elif position == 'SHORT':
                if rsi > rsi_long and prev_rsi < prev_rsi_long:
                    print(f"[{symbol}] time - {kiev_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    await place_order('BUY', symbol, dep, leverage, stop_loss, take_profit1, take_profit2, take_profit3, limit_percent, limit_x, client)
                    position = 'LONG'

            prev_rsi = rsi
            await asyncio.sleep(updating)

        except Exception as e:
            print(f"Ошибка в процессе торговли: {e}")
            await asyncio.sleep(updating)