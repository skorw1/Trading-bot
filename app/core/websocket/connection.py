import asyncio
from binance import BinanceSocketManager
from app.core.websocket.order_events import handle_socket_messages
async def monitor_take_profits(client):
    """
    Отслеживает исполнение тейк-профитов через WebSocket.
    """
    bsm = BinanceSocketManager(client)
    socket = bsm.futures_user_socket()

    async with socket as stream:
        print("WebSocket запущен. Ожидание событий...")
        try:
            while True:
                msg = await stream.recv()
                await handle_socket_messages(msg, client)
        except asyncio.CancelledError:
            print("Мониторинг тейк-профитов был остановлен.")
        except Exception as e:
            print(f"Ошибка в WebSocket: {e}")
            # здесь стоит переподключить WebSocket, если ошибка повторяется
            await asyncio.sleep(5)
            await monitor_take_profits(client)  # Попробовать переподключение