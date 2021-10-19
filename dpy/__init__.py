from .new_data import *
from aiohttp import ClientSession
from itertools import count
from json import dumps
from typing import Optional

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
