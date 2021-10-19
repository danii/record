from . import GatewayClient
from aiohttp.client_ws import ClientWebSocketResponse
from asyncio.exceptions import TimeoutError
from json import dumps, loads
from math import inf
from time import time_ns
from typing import Optional

class AIOHTTPGatewayManager:
	client: GatewayClient
	socket: ClientWebSocketResponse
	heartbeat_interval: Optional[int]
	waited: float

	def __init__(self, socket: ClientWebSocketResponse, *arguments):
		self.socket = socket
		self.client = GatewayClient(self, *arguments)
		self.heartbeat_interval = None
		self.waited = 0

	async def heartbeat_now(self):
		self.waited = inf

	async def send_str(self, data: str):
		await self.socket.send_str(data)

	async def run(self):
		default_timeout = 1000.0
		sequence: Optional[int] = None

		while True:
			this_interval = self.heartbeat_interval
			# If we don't know the interval yet, use default_timeout.
			timeout = default_timeout if this_interval is None \
				else this_interval - self.waited

			try:
				start = time_ns()
				message = loads(await self.socket.receive_str(timeout=timeout))
				if message["s"] is not None:
					print(sequence)
					sequence = message["s"]

				await self.client.process_payload(message)
				self.waited = self.waited + ((time_ns() - start) / 1000000)
				# We keep track of the time the processing took so we can keep track of
				# how much time has passed since the last heartbeat (or initial
				# connect).
			except TimeoutError:
				if this_interval is None:
					# The default_timeout has been reached. We don't send a heartbeat
					# because we only use default_timeout if we don't know the heartbeat
					# interval.
					self.waited = self.waited + default_timeout
					continue
				else:
					# If we timed out for any other reason then it must be because we hit
					# the heartbeat timeout, so time to pulse blood through our veins!
					print("Heartbeat", sequence)
					await self.send_str(dumps({"op": 1, "d": sequence}))
					self.waited = 0
