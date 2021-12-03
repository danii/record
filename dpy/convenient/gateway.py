from __future__ import annotations
from ..gateway import Event, process_payload
from ..ducks import JSON, CacheManager, GatewayManager as GatewayProtocol, \
	NetworkManagerWebsocket, type_check
from json import dumps, loads
from math import inf
from time import time_ns
from typing import Awaitable, Callable, Generic, Optional, TypeVar

_N = TypeVar("_N", bound=NetworkManagerWebsocket)

class GatewayManager(Generic[_N]):
	socket: _N

	heartbeat_interval: Optional[int]
	waited: float

	def __init__(self, socket: _N):
		self.socket = socket

		self.heartbeat_interval = None
		self.waited = 0

	async def heartbeat_now(self):
		self.waited = inf

	async def heartbeat_set(self, interval: int):
		self.heartbeat_interval = interval

	async def send(self, data: JSON):
		await self.socket.send(dumps(data))

	async def run(self, token: str, *,
			dispatch: Callable[[Event], Awaitable[None]],
			cache: Optional[CacheManager] = None):
		default_timeout = 1000.0
		sequence: Optional[int] = None

		while True:
			this_interval = self.heartbeat_interval
			# If we don't know the interval yet, use default_timeout.
			timeout = default_timeout if this_interval is None \
				else this_interval - self.waited

			try:
				start = time_ns()
				raw: str = str(await self.socket.receive(timeout=timeout))
				message = type_check(loads(raw), dict[str, JSON])
				if message["s"] is not None:
					if isinstance(message["s"], int) or isinstance(message["s"], float):
						sequence = type_check(message["s"], int)
					else:
						raise TypeError(f"expected type float or int, found type \
{type(message['s'])}")

				await process_payload(message, token,
					dispatch=dispatch, cache=cache, manager=self)
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
					await self.send({"op": 1, "d": sequence})
					self.waited = 0

_: type[GatewayProtocol] = GatewayManager
