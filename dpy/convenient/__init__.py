from __future__ import annotations
from typing import Union

from .cache import DefaultCache
from .dispatch import Dispatcher
from .aiohttp import AIOHTTPGatewayManager
from ..ducks import RunnableAsyncGatewayManager
from ..gateway import GatewayClient
from ..gateway.events import Event

ManagerArgument = Union[
	type[RunnableAsyncGatewayManager],
	RunnableAsyncGatewayManager
]

class Bot(DefaultCache, Dispatcher, GatewayClient):
	def __init__(self):
		DefaultCache.__init__(self)
		Dispatcher.__init__(self)
		GatewayClient.__init__(self, self.dispatch, self)

	async def run(self, token: str,
			manager: ManagerArgument = AIOHTTPGatewayManager):
		self.token = token

		if isinstance(manager, type):
			manager = await manager.connect("gateway.discord.gg")
		await manager.run(self)

