import requests_async as requests
import requests as _requests
requests.utils = _requests.utils
import time
import sys
import asyncio
import websockets
import json
import copy
from src.chess_data import ChessData
from src.subscriptions.all_subscriptions import *


class ChessClient (ChessData):

	def __init__(self, clientname, PHPSESSID = None):
		super().__init__(clientname)
		self._ws = None
		self.PHPSESSID = PHPSESSID
		self._session = requests.Session()
		self._is_running = False
		self._event_loop = None
		self._subscriptions = []
		self._id_events = {}
		self._send_data = []
		self._last_send_time = 0.0
		self._flushing_sends = False
		self.subscribe(ConnectSubscription.instance)
		self.subscribe(UserSubscription.instance)
		self.subscribe(ChallengeSubscription(self))
		self.subscribe(ListeningSubscription(self, "/game", GameSubscription))

	def subscribe(self, subscription):
		assert issubclass(type(subscription), Subscription)
		self._subscriptions.append(subscription)
		return subscription

	def unsubscribe(self, subscription): 
		self._subscriptions.remove(subscription)

	def is_running(self):
		return self._is_running

	def stop(self):
		self._is_running = False

	async def short_sleep(self):
		await asyncio.sleep(0.2)

	async def wait_init(self):
		while self._client_id == None or self.username == None:
			await self.short_sleep()

	def run(self, *args, **kwargs):
		if self._event_loop == None:
			self._event_loop = asyncio.get_event_loop()
		self._event_loop.run_until_complete(self._run_loop(*args, **kwargs))

	async def _dispatch_event(self, event):
		self.log(f"DISPATCHING ({event['channel']}):")
		if "id" in event:
			id = int(event["id"])
			assert id not in self._id_events
			self._id_events[id] = copy.deepcopy(event)
		if not any([event["channel"].startswith(channel) for channel in self.NOLOG_CHANNELS]):
			self.log_json(event)
		else:
			self.log("(IGNORED)")
		valid_subscriptions = []
		for subscription in self._subscriptions:
			if subscription._event_is_valid(event):
				valid_subscriptions.append(subscription)
		for subscription in valid_subscriptions:
			await subscription._dispatch(copy.deepcopy(event), self)
		self.log(f"DISPATCHED TO {len(valid_subscriptions)} SUBSCRIPTIONS\n")
		return len(valid_subscriptions)

	async def _raw_send(self, data):
		if len(data) != 0:
			self.log("RAW SEND")
		if self._ws == None:
			self._ws = await websockets.connect(self.COMETD_WEBSOCKET, extra_headers = {"cookie" : f"PHPSESSID={self.PHPSESSID}"})
		for i in data:
			await self._ws.send(json.dumps(i))
			with open("log2.txt", "a") as f:
				f.write(f"SEND ({time.time()}):\n")
				f.write(json.dumps(i, indent = 1, sort_keys = True))
				f.write("\n\n")
		#r = await self._session.post(self.COMETD_URL, json = data)
		res = []
		while True:
			try:
				d = await asyncio.wait_for(self._ws.recv(), timeout = 0.1)
				res.extend(json.loads(d))
			except asyncio.TimeoutError:
				break
		if len(res) != 0:
			self.log(res)
		for i in res:
			with open("log2.txt", "a") as f:
				f.write(f"GET ({time.time()}):\n")
				f.write(json.dumps(i, indent = 1, sort_keys = True))
				f.write("\n\n")
		#self.log("ALL RECIEVED:")
		#for i in r.json():
			#self.log_json(i)
			#self.log("")
		return res

	def exec_async(self, coro):
		return self._event_loop.create_task(coro)

	async def send(self, channel, data):
		data = copy.deepcopy(data)
		if channel != None:
			data["channel"] = channel
		self.log("GETTING READY TO SEND MESSSAGE:")
		self.log_json(data)
		assert "channel" in data
		self._send_data.append(data)
		await self._flush_sends()
		id = int(data["id"])
		while id not in self._id_events:
			await self.short_sleep()
			await self._flush_sends()
		ret = self._id_events[id]
		del self._id_events[id]
		return ret

	async def _do_handshake(self):
		handshake_event = await self.send(self.HANDSHAKE_CHANNEL, self._get_handshake_data())
		if not handshake_event["successful"]:
			self.log(f"HANDSHAKE FAILED")
			self.stop()
			return
		self._client_id = handshake_event["clientId"]
		self.log(f"HANDSHAKE COMPLETE")
		self.log(f"client_id = {self._client_id}")

	async def _flush_sends(self):
		if self._flushing_sends:
			return
		self._flushing_sends = True
		self.log("=" * 50)
		if len(self._send_data) == 0:
			await self.short_sleep()
		send_data = self._send_data
		self._send_data = []
		self._last_send_time = time.time()
		events = await self._raw_send(send_data)
		self._flushing_sends = False
		for event in events:
			await self._dispatch_event(copy.deepcopy(event))
		self.exec_async(self._flush_sends())

	async def _run_loop(self, PHPSESSID = None):
		if PHPSESSID != None:
			self.PHPSESSID = PHPSESSID
		assert self.PHPSESSID != None
		#self._session.cookies.set("PHPSESSID", PHPSESSID)
		self._is_running = True
		await self._do_handshake()
		while self._is_running:
			await self.short_sleep()




