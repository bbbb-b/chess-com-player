#!/usr/bin/python3

from src.chess_client import ChessClient
import asyncio

def main():
	chess_client = ChessClient("<doesnt matter>")
	with open("PHPSESSID", "r") as f:
		PHPSESSID = f.read().strip()
	chess_client.run(PHPSESSID = PHPSESSID)




if __name__ == "__main__":
	main()
