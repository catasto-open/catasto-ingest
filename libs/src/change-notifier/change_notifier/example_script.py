import asyncio
from reftree_notifier import ReftreeNotifier

async def notifier_start():
    # Replace the placeholder values with your actual connection details
    host='http://memphis_host_name'
    username='root'
    connection_token='memphis'
    station_name='reftree'
    producer_name='reftree'

    notifier = ReftreeNotifier(host, username, connection_token, station_name, producer_name)

    await notifier.notify()


asyncio.run(notifier_start())
