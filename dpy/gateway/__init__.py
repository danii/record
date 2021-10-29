from __future__ import annotations
from .events import *
from ..data import *
from ..ducks import CacheManager, GatewayManager
from json import dumps
from typing import Awaitable, Callable, Optional

class GatewayClient:
	token: str
	manager: GatewayManager
	dispatch: Callable[[Event], Awaitable]
	cache: Optional[CacheManager]

	def __init__(self, manager: GatewayManager, token: str,
			dispatch: Callable[[Event], Awaitable],
			cache: Optional[CacheManager] = None):
		self.token = token
		self.manager = manager
		self.dispatch = dispatch
		self.cache = cache

	async def process_payload(self, payload):
		op_code: int = payload["op"]
		data: Any = payload["d"]

		if op_code == 0: # Dispatch
			event: str = payload["t"]

			if event == "READY":
				user = SelfUser._from_api(self.cache, data["user"])
				guilds = [Guild._from_api(self.cache, guild) \
					for guild in data["guilds"]]

				if self.cache is not None:
					for guild in guilds:
						self.cache.cache_guild(guild)
					self.cache.cache_user()

				await self.dispatch(ReadyEvent(user, guilds))
			elif event == "GUILD_CREATE":
				guild = AvailableGuild._from_api(self.cache, data)

				if self.cache is not None:
					self.cache.cache_guild(guild)

				await self.dispatch(GuildCreateEvent(guild))
			elif event == "MESSAGE_CREATE":
				message = Message._from_api(self.cache, data)

				# TODO: CACHE

				await self.dispatch(MessageCreateEvent(message))
		elif op_code == 1:
			await self.manager.heartbeat_now()
		elif op_code == 10: # Hello!
			self.manager.heartbeat_interval = data["heartbeat_interval"]

			await self.manager.send_str(dumps({
				"op": 2,
				"d": {
					"token": self.token,
					"properties": {
						"$os": "linux",
						"$browser": "an unnamed in-dev Discord library",
						"$device": "an unnamed in-dev Discord library"
					},
					"compress": False,
					"intents": 0b111111111111111
				}
			}))
