"""Implementations of the event loop and mixins of the library's constructs to
make a convenient and easy to use "bot" class.
"""

from __future__ import annotations
from types import TracebackType
from .cache import DefaultCache
from .dispatch import BasicDispatcher
from .gateway import GatewayManager
from .managers import AIOHTTPNetworkManager
from ..ducks import NetworkManager
from typing import Optional, TypeVar

_E = TypeVar("_E", bound=BaseException)

class Bot(DefaultCache, BasicDispatcher):
	_networking: NetworkManager

	def __init__(self, *, networking: Optional[NetworkManager] = None):
		self._networking = AIOHTTPNetworkManager() if networking is None \
			else networking
		DefaultCache.__init__(self)
		BasicDispatcher.__init__(self)

	async def __aenter__(self):
		await self._networking.__aenter__()
		return self

	async def __aexit__(self, exception_type: type[_E], exception: _E,
			traceback: TracebackType):
		await self._networking.__aexit__(exception_type, exception, traceback)

	async def run(self, token: str):
		async with await self._networking.request_websocket("wss://gateway.discord.gg/") \
				as socket:
			await GatewayManager(socket).run(token, dispatch=self.dispatch)
