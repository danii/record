from __future__ import annotations
from ..gateway import GatewayClient
from aiohttp import ClientSession
from aiohttp.client_ws import ClientWebSocketResponse
from asyncio.exceptions import TimeoutError
from json import dumps, loads
from math import inf
from time import time_ns
from typing import Optional

class AIOHTTPGatewayManager:
	socket: ClientWebSocketResponse

	heartbeat_interval: Optional[int]
	waited: float

	@classmethod
	async def connect(cls, base: str) -> AIOHTTPGatewayManager:
		socket = await ClientSession().ws_connect(f"wss://{base}?v=9&encoding=json")
		return cls(socket)

	def __init__(self, socket: ClientWebSocketResponse):
		self.socket = socket

		self.heartbeat_interval = None
		self.waited = 0

	async def heartbeat_now(self):
		self.waited = inf

	async def send_str(self, data: str):
		await self.socket.send_str(data)

	async def run(self, client: GatewayClient):
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
					sequence = message["s"]

				await client.process_payload(self, message)
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
					await self.send_str(dumps({"op": 1, "d": sequence}))
					self.waited = 0
