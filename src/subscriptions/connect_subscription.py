from src.chess_data import ChessData
from src.subscriptions.subscription import Subscription
import asyncio


class ConnectSubscription(Subscription):
	PING_INTERVAL = 1.0 # i think it should be 10 seconds but who cares
	def __init__(self):
		super().__init__(None, [ChessData.HANDSHAKE_CHANNEL])

	def callback(self, event, client):
		client.exec_async(self.ping_loop(client))

	async def ping_loop(self, client):
		await client.wait_init()
		while client.is_running():
			connect_event = await client.send(client.CONNECT_CHANNEL, client._get_connect_data())
			await asyncio.sleep(self.PING_INTERVAL)

ConnectSubscription.instance = ConnectSubscription()
