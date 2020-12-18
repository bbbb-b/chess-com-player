from src.subscriptions.subscription import Subscription

class ListeningSubscription(Subscription):
	def __init__(self, client, channel_start, cls):
		super().__init__(client, client.USER_CHANNEL, "Subscribe", instant = True)
		self.channel_start = channel_start
		self.cls = cls
		self._subscribed_channels = set()

	def callback(self, event, client):
		channels = event["data"]["channel"]
		if type(channels) is str:
			channels = [channels]
		for channel in channels:
			assert channel not in self._subscribed_channels
			if channel.startswith(self.channel_start) and channel not in self._subscribed_channels:
				self._subscribed_channels.add(channel)
				client.subscribe(self.cls(client, channel))
