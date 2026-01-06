import aiohttp

async def get_data_local(symbol, interval, limit):
    url = f'http://localhost:8000/data?symbol={symbol}&interval={interval}'
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    json_data = await response.json()
                    data = json_data.get('data', [])
                    if not data:
                        return None
                    data = data[-limit:] if limit and len(data) >= limit else data
                    open_prices = [float(c[1]) for c in data]
                    high_prices = [float(c[2]) for c in data]
                    low_prices = [float(c[3]) for c in data]
                    close_prices = [float(c[4]) for c in data]
                    return open_prices, high_prices, low_prices, close_prices
                else:
                    return None
        except Exception:
            return None