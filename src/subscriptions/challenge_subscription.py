from src.subscriptions.subscription import Subscription
from src.chess_data import ChessData
import string
import random
import asyncio

valid_symbols = string.ascii_lowercase + string.digits

def _get_uuid(length):
	return "".join([random.choice(valid_symbols) for i in range(length)])

# basically just creates a challenge and lets a passive listener play it
class ChallengeSubscription(Subscription):
	def __init__(self, client):
		super().__init__(client, "")
		self.challenge_uuid = None
		self.challenge_id = None
		self.enemy_username = None
		self.self_subscribe(client.GAME_CHANNEL, "ChallengeList", self.challenge_list_callback)
		self.self_subscribe(client.GAME_CHANNEL, ["Challenge", "ChallengeAccept", "ChallengeFail"],
			self.challenge_callback)

	def challenge_list_callback(self, event, client):
		challenges = event["data"]["challenges"]
		assert len(challenges) <= 1
		found = False
		for challenge in challenges:
			if challenge["from"]["uid"] == client.username:
				found = True
				self.accept_challenge(challenges)
				break
		if not found:
			client.exec_async(self.create_challenge())

	def accept_challenge(self, challenge):
		self.client.log("TAKING OLD CHALLENGE")
		self.challenge_id = challenge["id"]

	async def create_challenge(self, timeout = 0):
		self.challenge_uuid = None
		self.challenge_id = None
		self.enemy_username = None
		await asyncio.sleep(timeout)
		self.challenge_uuid = _get_uuid(7)
		self.client.log(f"challenge uuid = {self.challenge_uuid}")
		await self.client.wait_init()
		await self.client.send(self.client.GAME_CHANNEL, self.client._get_search_game_data(self.challenge_uuid))

	async def challenge_callback(self, event, client):
		data = event["data"]
		if data["tid"] == "Challenge":
			if "uuid" in data["challenge"]:
				if data["challenge"]["uuid"] == self.challenge_uuid:
					if self.challenge_id != None:
						client.log("challenge appearing twice, id should be same?...")
						assert self.challenge_id == data["challenge"]["id"]
					self.challenge_id = data["challenge"]["id"]
				else:
					client.log("challenge shown but uuid is different, ignoring")
		elif data["tid"] == "ChallengeAccept":
			if self.challenge_id == data["challenge"]["id"]:
				if self.enemy_username != None:
					client.log("challengeaccept appearing twice, enemy username should be same?...")
					assert self.enemy_username == data["challenge"]["by"]
				self.enemy_username = data["challenge"]["by"]
				await self.create_challenge(20)
				#self.unsubscribe()
			else:
				client.log("challenge accept but challenge id different, ignoring")
		elif data["tid"] == "ChallengeFail":
			client.log("CHALLENGE FAIL...")
			if data["codemessage"] == "user.playing_game":
				await self.create_challenge(20)
			elif data["codemessagE"] == "game.not_active":
				await self.create_challenge(10)
			else:
				client.stop()
		else:
			assert False
