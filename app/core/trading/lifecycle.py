import asyncio
from app.core.trading.state import tasks
from app.core.trading.trade_loop import trade
from app.database import get_currency_pair
from app.infrastructure.config import DATABASE_PATH
from app.infrastructure.telegram import safe_answer

async def start_trading(message, symbol, strategy_name):

    # receiving data from db
    print(symbol, strategy_name)
    pair_info = await get_currency_pair(DATABASE_PATH, symbol, strategy_name)
    if not pair_info:
        await safe_answer(message, "Пара не знайдена в базі даних.")
        return

    updating = pair_info[3]
    timeframe = pair_info[4]
    dep = pair_info[5]
    leverage = pair_info[6]
    rsi_long = pair_info[7]
    prev_rsi_long = pair_info[8]
    rsi_short = pair_info[9]
    prev_rsi_short = pair_info[10]
    rsi_period = pair_info[11]
    rsi_type = pair_info[12]
    stop_loss = pair_info[13]
    take_profit1 = pair_info[14]
    take_profit2 = pair_info[15]
    take_profit3 = pair_info[16]
    limit_percent = pair_info[17]
    limit_x = pair_info[18]

    await asyncio.sleep(0.5)

    if (symbol, strategy_name) not in tasks:
        task = asyncio.create_task(trade(symbol, updating, timeframe, dep, leverage, rsi_long, prev_rsi_long, rsi_short, prev_rsi_short, rsi_period, rsi_type, stop_loss, take_profit1, take_profit2, take_profit3, limit_percent, limit_x))
        tasks[(symbol, strategy_name)] = task
        await safe_answer(message, f"Запущена торгівля для {symbol}.")
    else:
        await safe_answer(message, f"Торгівля для {symbol} вже запущена.")

async def stop_trading(message, symbol, strategy_name):
    if (symbol, strategy_name) in tasks:
        tasks[(symbol, strategy_name)].cancel()
        del tasks[(symbol, strategy_name)]
        print(f'stop trading for {symbol}')
        await safe_answer(message, f"Зупинка торгівлі для {symbol}.")
    else:
        await safe_answer(message, f"Торгівля для {symbol} не була запущена.")
