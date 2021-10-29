from __future__ import annotations
from ..data import *
from ..new_data import *
from aiohttp import ClientSession
from itertools import count
from json import dumps
from typing import Optional

class RESTClient:
	_token: str
	base = "https://discord.com/api/v9"
	session: ClientSession

	def __init__(self, token: str, session: Optional[ClientSession] = None):
		self._token = token
		self.session = session or ClientSession()

	async def __aenter__(self):
		await self.session.__aenter__()
		return self

	async def __aexit__(self, exception_type, exception, traceback):
		await self.session.__aexit__(exception_type, exception, traceback)

	async def create_guild(self, guild: NewGuild) -> AvailableGuild:
		endpoint = f"{self.base}/guilds"
		print(endpoint)
		data = dumps(guild._to_api())
		headers = {
			"content-type": "application/json",
			"authorization": self._token
		}

		async with self.session.post(endpoint, data=data, headers=headers) \
				as response:
			return AvailableGuild._from_api(None, await response.json())

	async def delete_guild(self, guild: Union[AvailableGuild, int]):
		guild: int = guild.id if isinstance(guild, AvailableGuild) else guild
		endpoint = f"{self.base}/guilds/{guild}"
		headers = {
			"authorization": self._token
		}

		async with self.session.delete(endpoint, headers=headers):
			pass

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

	async def create_message(self, channel: Union[TextChannel, int],
			message: NewMessage):
		channel: int = channel.id if isinstance(channel, TextChannel) else channel
		endpoint = f"{self.base}/channels/{channel}/messages"
		data = dumps(message._to_api())
		headers = {
			"content-type": "application/json",
			"authorization": self._token
		}

		async with self.session.post(endpoint, data=data, headers=headers) as r:
			print(await r.json())
			print(r.status)
