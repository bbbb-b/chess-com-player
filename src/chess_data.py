import time
import sys
import json

class ChessData:
	BASE_URL = "https://www.chess.com"
	LIVE_BASE_URL = "https://live.chess.com"
	HOME_URL = BASE_URL + "/home"
	COMETD_URL = "https://live2.chess.com/cometd"
	COMETD_WEBSOCKET = "wss://live2.chess.com/cometd"
	LOGIN_URL = BASE_URL + "/login"
	LOGIN_CHECK_URL = BASE_URL + "/login_check"
	#HANDSHAKE_URL = LIVE_BASE_URL + "/cometd/handshake"
	

	CONNECT_CHANNEL = "/meta/connect"
	HANDSHAKE_CHANNEL = "/meta/handshake"
	GAME_CHANNEL = "/service/game"
	USER_CHANNEL = "/service/user"
	SUBSCRIBE_CHANNEL = "/meta/subscribe"
	UNSUBSCRIBE_CHANNEL = "/meta/unsubscribe"

	NOLOG_CHANNELS = [
		#"/chat",
		#"/meta/connect",
		#"/announce",
	]

	def __init__(self, clientname):
		self._connection_type = "ssl-websocket"
		self._clientname = clientname
		self._last_connection_id = 0
		self._client_id = None
		self._ack = True
		self.username = None

	def log(self, msg):
		print (f"[{time.time()}]", file = sys.stderr)
		print(str(msg), file = sys.stderr) # if adding custom log file, then dont forget to flush
		sys.stderr.flush()
		with open("log.txt", "a") as f:
			print(str(msg), file = f) # if adding custom log file, then dont forget to flush
			f.flush()

	def log_json(self, data):
		return self.log(json.dumps(data, indent = 1, sort_keys = True))

	def _get_connection_id(self):
		self._last_connection_id += 1
		return str(self._last_connection_id)

	def _get_login_data(self, username, password, logintoken):
		return {
			"_username" : username,
			"_password" : password,
			"login" : "",
			"_target_path" : "https://www.chess.com/",
			"_token" : login_token
		}

	def _get_timesync_data(self):
		return {
			"l" : 0,
			"o" : 0,
			"tc" : round(time.time() * 1e3)
		}

	def _get_ext_data(self):
		old_ack = self._ack
		if self._ack is True:
			self._ack = 1
		else:
			self._ack += 1
		return {
			"ack" : (old_ack),
			"timesync" : self._get_timesync_data()
		}

	def _get_connect_data(self):
		return {
			"ext" : self._get_ext_data(),
			"connectionType" : self._connection_type,
			"id" : self._get_connection_id(),
			"clientId" : self._client_id
		}

	def _get_handshake_data(self):
		return {
			"advice" : {
				"interval" : 0,
				"timeout" : 60000
			},
			#"channel" : self.HANDSHAKE_CHANNEL
			"clientFeatures" : {
				"protocolversion" : "2.1",
				"clientname" : "LC6;" + "k12s7k3",
				"adminservice" : True,
				"announceservice" : True,
				"areas" : True,
				"chessgroups" : True,
				"events" : True,
				"examineboards" : True,
				"gameobserve" : True,
				"genericchatsupport" : True,
				"genericgamesupport" : True,
				"guessthemove" : True,
				"multiplegames" : True,
				"multiplegamesobserve" : True,
				"pingservice" : True,
				"playbughouse" : True,
				"playchess" : True,
				"playchess960" : True,
				"playcrazyhouse" : True,
				"playkingofthehill" : True,
				"playoddchess" : True,
				"playthreecheck" : True,
				"privatechats" : True,
				"stillthere" : True,
				"teammatches" : True,
				"tournaments" : True,
				"userservice" : True,
				"offlinechallenges" : True
			},
			"clientId" : self._client_id,
			"ext" : self._get_ext_data(),
			"id" : self._get_connection_id(),
			"minimumVersion" : "1.0",
			"serviceChannels" : [
				"/service/user"
			],
			"supportedConnectionTypes" : [
				self._connection_type
			],
			#"options" : [], # GONE!
			"version" : "1.0"
		}
	
	def _get_search_game_data(self, challenge_uuid):
		return {
			"channel" : self.GAME_CHANNEL,
			"data" : {
				"basetime" : 600, # minute * 60 * 10 (????) 
				"timeinc" : 0,
				"uuid" : challenge_uuid,
				"from" : self.username,
				#"to" : None,
				#"initpos" : None,
				"gametype" : "chess",
				"rated" : True,
				"minrating" : 1000,
				"maxrating" : 2000,
				"sid" : "gserv",
				"tid" : "Challenge"
			},
			"id" : self._get_connection_id(),
			"clientId" : self._client_id
		}
	
	def _get_game_move_data(self, move, game):
		return {
			"data" : {
				"tid" : "Move",
				"move" : {
					# enemy clock ??? 
					"clock" : game["clocks"][int(game["players"][1] == self.username)],
					"clockms" : game["clocks"][int(game["players"][1] == self.username)] * 1000,
					"coh" : False,
					"gid" : game["id"],
					"lastmovemessagesent" : False,
					"mht" : 1000,
					"move" : move,
					"seq" : game["seq"],
					"squared" : True,
					"uid" : self.username
				}
			},
			"clientId" : self._client_id,
			"id" : self._get_connection_id(),
		}
