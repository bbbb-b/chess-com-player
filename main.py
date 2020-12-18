#!/usr/bin/python3

from src.chess_client import ChessClient
import asyncio

def main():
	chess_client = ChessClient("<doesnt matter>")
	#PHPSESSID = "ce0d754717da4fed255ffbc912e4bc93"
	#PHPSESSID = "df12997458d934328d73875e3501ecd3"
	#PHPSESSID = "09969431f2d0f3814c49e8e2c8f431ac"
	#PHPSESSID = "261ebd866eeef47930ede278b4e9831e"
	with open("PHPSESSID", "r") as f:
		PHPSESSID = f.read().strip()
	chess_client.run(PHPSESSID = PHPSESSID)




if __name__ == "__main__":
	main()
