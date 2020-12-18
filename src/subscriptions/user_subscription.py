from src.subscriptions.subscription import Subscription
from src.chess_data import ChessData

class UserSubscription(Subscription):
	def __init__(self):
		super().__init__(None, ChessData.USER_CHANNEL, "User")

	def callback(self, event, client):
		client.username = event["data"]["user"]["uid"]

UserSubscription.instance = UserSubscription()
