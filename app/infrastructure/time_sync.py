import time

async def check_time(client):
    # Getting server time
    server_time_data = await client.get_server_time()
    server_time = server_time_data['serverTime']

    # Local time in milliseconds
    local_time = int(time.time() * 1000)

    # Calculation of the difference
    time_diff = server_time - local_time

    print(f"Server time: {server_time}, Local time: {local_time}")
    print(f"Time difference: {time_diff} ms")

    if abs(time_diff) > 1000:
        print("Time difference is too large")