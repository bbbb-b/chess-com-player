import time
import asyncio
from src.chess_data import ChessData

class Subscription:
	def __init__(self, client, channels, tids = None, callback = None, instant = False):
		self.client = client
		self.channels = channels if (type(channels) is list or channels == None) else [channels]
		self.tids = tids if (type(tids) is list or tids == None) else [tids]
		self.instant = instant
		self.used_subscriptions = []
		if callback != None:
			self.callback = callback

	def _event_is_valid(self, event):
		valid = True
		valid &= self.channels == None or event["channel"] in self.channels
		valid &= self.channels == None or any(event["channel"].startswith(channel) for channel in self.channels)
		valid &= self.tids == None or ("data" in event and event["data"]["tid"] in self.tids)
		return valid

	async def _dispatch(self, event, client):
		assert(self._event_is_valid(event))
		if asyncio.iscoroutinefunction(self.callback):
			if self.instant:
				await self.callback(event, client)
			else:
				client.exec_async(self.callback(event, client))
		else:
			self.callback(event, client)
		return True

	def callback(self, event, client):
		assert False

	def unsubscribe(self):
		assert self.client != None
		for subscription in self.used_subscriptions:
			subscription.unsubscribe()
		self.client.unsubscribe(self)

	def self_subscribe(self, *args, **kwargs):
		self.used_subscriptions.append(self.client.subscribe(Subscription(self.client, *args, **kwargs)))
		return self.used_subscriptions[-1]

	def __eq__(self, other):
		return id(self) == id(other)
		if id(self) == id(other):
			return True
		if type(self) != type(other):
			return False
		if self.channels != other.channels:
			return False
		if self.tids != other.tids:
			return False
		if self.callback != other.callback:
			return False
		return True

	def __ne__(self, other):
		return not (self == other)
