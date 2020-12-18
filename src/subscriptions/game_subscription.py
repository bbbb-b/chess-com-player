import math
import time
import asyncio
import pwn
import sys
import copy
import time
import json

from src.subscriptions.subscription import Subscription

# subscribes to all games and players

class ChessState:
	POSITION_BOARD = [ # maybe invert this shit later
		"456789!?",
		"WXYZ0123",
		"OPQRSTUV",
		"GHIJKLMN",
		"yzABCDEF",
		"qrstuvwx",
		"ijklmnop",
		"abcdefgh"
	]
	PROMOTION_QUEEN = ("{", "~", "}")
	NONE = 0
	PAWN = 1
	KNIGHT = 2
	BISHOP = 3
	ROOK = 4
	QUEEN = 5
	KING = 6
	ASCII_TRANSLATE = [" ", "p", "b", "k", "r", "Q", "K"]

	def __init__(self): # board is [x, y]
		self.board = [] 
		self.board.append([-self.ROOK, -self.KNIGHT, -self.BISHOP,
			-self.QUEEN, -self.KING, -self.BISHOP, -self.KNIGHT, -self.ROOK])
		self.position_board = copy.deepcopy(self.POSITION_BOARD)
		self.board.append([-self.PAWN] * 8)
		self.inverted = False
		for i in range(4):
			self.board.append([self.NONE] * 8)
		self.board.append([self.PAWN] * 8)
		self.board.append([self.ROOK, self.KNIGHT, self.BISHOP,
			self.QUEEN, self.KING, self.BISHOP, self.KNIGHT, self.ROOK])

	def invert(self):
		#self.board = list(map(lambda x : [-y for y in x][::-1], self.board))[::-1]
		self.inverted = not self.inverted
		self.position_board = list(map(lambda x : x[::-1], self.position_board))[::-1]
		# replace king with queen
		self.board[0] = self.board[0][::-1]
		self.board[7] = self.board[7][::-1]

	def tuple_to_move(self, move):
		ret = [self.position_board[move[0][0]][move[0][1]], self.position_board[move[1][0]][move[1][1]]]
		if abs(self[move[0]]) == self.PAWN and move[1][0] in (0, 7):
			ind = (move[1][1] - move[0][1])
			if self.inverted:
				ind = -ind
			ret[1] = self.PROMOTION_QUEEN[ind + 1]
		return "".join(ret)

	def move_to_tuple(self, move):
		assert len(move) == 2
		ret = [None, None, self.QUEEN]
		for x in range(8):
			for y in range(8):
				for i in range(2):
					if self.position_board[y][x] == move[i]:
						ret[i] = (y, x)
		assert ret[0] != None
		# promotion symbol
		if ret[1] == None:
			assert move[1] in self.PROMOTION_QUEEN
			add = self.PROMOTION_QUEEN.index(move[1]) - 1
			if self.inverted:
				add = -add
			ret[1] = (7 if ret[0][0] == 6 else 0, ret[0][1] + add)

		ret[2] = int(math.copysign(ret[2], self[ret[0]]))
		#assert ret[0] != None and ret[1] != None
		return ret

	def make_move(self, move):
		if type(move) is str:
			move = self.move_to_tuple(move)
		# pawn move to diff x without killing
		if abs(self[move[0]]) == self.PAWN and move[0][1] != move[1][1] and self[move[1]] == self.NONE:
			remove_at = (move[0][0], move[1][1])
			assert self[remove_at] != self.NONE
			self[remove_at] = self.NONE
		self[move[1]] = self[move[0]]
		self[move[0]] = self.NONE
		# pawn is promoted
		if abs(self[move[1]]) == self.PAWN and move[1][0] in (0, 7): 
			self[move[1]] = move[2]
		# king moves 2 in x
		if abs(self[move[1]]) == self.KING and abs(move[0][1] - move[1][1]) == 2:
			y = move[0][0]
			x1 = (7 if (move[1][1] > move[0][1]) else 0) # rook x
			x2 = move[1][1] + (-1 if x1 == 7 else 1) # rook new x
			self[y, x2] = self[y, x1]
			self[y, x1] = self.NONE

	def to_str(self, pretty):
		ret = []
		if pretty:
			ret.append("  ")
			for i in range(8):
				ret.append(f"  {i}")
			ret.append("\n")
		for y in range(8):
			if pretty:
				ret.append(chr(ord('A') + y) + " ")
			for x in range(8):
				ret.append(" ")
				if pretty:
					if self[y, x] < 0:
						ret.append("-")
					else:
						ret.append(" ")
					ret.append(self.ASCII_TRANSLATE[abs(self[y, x])])
				else:
					ret.append(str(self[y, x]))
			ret.append("\n")
		return "".join(ret)

	def __str__(self):
		return self.to_str(pretty = True)

	def __getitem__(self, key):
		return self.board[key[0]][key[1]]

	def __setitem__(self, key, value):
		self.board[key[0]][key[1]] = value

class GameSubscription(Subscription):
	def __init__(self, client, channel):
		super().__init__(client, channel, ["FullGame", "GameState"], self.game_callback)
		self.self_subscribe(client.GAME_CHANNEL, ["MoveFail", "EndGame"], self.game_channel_callback)
		self.last_seq = -1
		self.made_moves = ""
		self.game_id = None
		self.player_index = None
		self.chess_state = ChessState()

	def process_moves(self, moves):
		for i in range(len(self.made_moves), len(moves), 2):
			self.chess_state.make_move(moves[i:i+2])
		self.made_moves = moves

	async def game_channel_callback(self, event, client):
		client.log(f"GAME CHANNEL CALLBACK ({time.time()})")
		client.log_json(event)
		data = event["data"]
		if data["tid"] == "MoveFail":
			if self.game_id == data["gid"]:
				client.stop()
				#await self.make_move()
		elif data["tid"] == "EndGame":
			if self.game_id == data["game"]["id"]:
				client.log("END GAME")
				self.unsubscribe()
				with open("end_game_data.txt", "a") as f:
					f.write(json.dumps(event, indent = 1, sort_keys = True))
					f.write("\n\n")
				if self.last_seq != -1:
					pass
					#client.stop()

	def get_bot_move(self):
		p = pwn.process("./cpplayer", stderr = sys.stderr)
		self.client.log(self.chess_state.to_str(False))
		p.send(self.chess_state.to_str(False))
		move = p.readline().strip().decode() # decode cuz it gives bytes
		self.client.log(move)
		tuple_move = []
		for i in range(0, 4, 2):
			tuple_move.append((ord(move[i]) - ord('a'), ord(move[i+1]) - ord('1')))
		tuple_move.append(self.chess_state.QUEEN)
		self.client.log(tuple_move)
		p.close()
		return self.chess_state.tuple_to_move(tuple_move)

	async def make_bot_move(self):
		self.client.log(f"MAKING MOVE with last_seq = {self.last_seq}, last_game_seq = {self._last_game['seq']}")
		await self.client.send(self.client.GAME_CHANNEL,
			self.client._get_game_move_data(self.get_bot_move(), self._last_game))
		self.client.log(f"SEND MOVE DONE ({time.time()})")

	async def game_callback(self, event, client):
		client.log(f"PLAYER CALLBACK ({time.time()})")
		client.log_json(event)
		data = event["data"]
		game = data["game"]
		if data["tid"] == "FullGame":
			assert self.game_id == None or self.game_id == game["id"]
			self.game_id = game["id"]
			assert self.player_index == None
			if self.player_index == None:
				self.player_index = int(game["players"][1]["uid"] == client.username)
				if self.player_index == 1:
					self.chess_state.invert()
		elif data["tid"] == "GameState":
			if game["seq"] > self.last_seq:
				self._last_game = game
				self.last_seq = game["seq"]
				self.process_moves(game["moves"])
				if (self.last_seq) % 2 == self.player_index:
					await self.make_bot_move()
		client.log(f"recvd event {data['tid']}")
		client.log(self.chess_state)

