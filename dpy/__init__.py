from .data import *
from .events import *
from .new_data import *
from aiohttp import ClientSession
from itertools import count
from json import dumps, loads
from typing import Callable, Optional, Protocol

class RESTClient:
	_token: str
	session: ClientSession

	def __init__(self, token: str, session: Optional[ClientSession] = None):
		self._token = token
		self.session = session or ClientSession()

	async def __aenter__(self):
		await self.session.__aenter__()
		return self

	async def __aexit__(self, exception_type, exception, traceback):
		await self.session.__aexit__(exception_type, exception, traceback)

	async def create_guild(self, guild: NewGuild):
		data = dumps(guild._to_api())
		await self.session.post(
			"https://discord.com/api/v9/guild",
			data=data,
			headers={
				"content-type": "application/json",
				"authorization": self._token
			}
		)

	async def create_guild_channel(self, guild: int, channel: NewGuildChannel):
		async with self.session.post(
					f"https://discord.com/api/v9/guilds/{guild}/channels",
					data=dumps(channel._to_api(count())),
					headers={
						"content-type": "application/json",
						"authorization": self._token
					}
				) as session:
			print(session)

# class WebSocketLike(Protocol):
# 	async def send_str(self, data: str): ...
# 	async def send_bytes(self, data: bytes): ...
# 	async def receive(self) -> : ...

class GatewayManager(Protocol):
	heartbeat_interval: Optional[int]

	async def heartbeat_now(self): ...
	async def send_str(self, data: str): ...
	async def send_bytes(self, data: bytes): ...

class CacheManager(Protocol):
	async def cache_guild(self, guild: Guild): ...
	async def cache_user(self, user): ...

class GatewayClient:
	token: str
	manager: GatewayManager
	dispatch: Callable[[Event], None]
	cache: Optional[CacheManager]

	def __init__(self, manager: GatewayManager, token: str,
			dispatch: Callable[[Event], None], cache: Optional[CacheManager] = None):
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
				user = SelfUser._from_api(data["user"])
				guilds = [Guild._from_api(guild) for guild in data["guilds"]]

				if self.cache is not None:
					for guild in guilds:
						self.cache.cache_guild(guild)
					self.cache.cache_user()

				self.dispatch(ReadyEvent(user, guilds))
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
