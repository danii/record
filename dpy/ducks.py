from __future__ import annotations
from types import TracebackType
from .data import *
from typing import Any, Optional, Protocol, Union, TypeVar, cast, get_origin

_T = TypeVar("_T")
_E = TypeVar("_E", bound=BaseException)
_AsyncWithSelf = TypeVar("_AsyncWithSelf", bound="AsyncWith")
JSON = Union[dict[str, "JSON"], list["JSON"], str, int, float, bool, None]

def type_check(value: Any, check: type[_T]) -> _T:
	origin = cast(type[_T], check if get_origin(check) is None \
		else get_origin(check))

	if isinstance(value, origin):
		return value
	else:
		raise TypeError(f"expected type {check}, found type {type(value)}")

class AsyncWith(Protocol):
	async def __aenter__(self: _AsyncWithSelf) -> _AsyncWithSelf: ...
	async def __aexit__(self, exception_type: type[_E], exception: _E,
			traceback: TracebackType): ...

class NetworkManager(AsyncWith, Protocol):
	async def request(self, url: str, *,
			method: str = "GET",
			data: Optional[Union[str, bytes]] = None,
			headers: dict[str, str] = {}) -> NetworkManagerResponse: ...

	async def request_websocket(self, url: str) -> NetworkManagerWebsocket: ...

class NetworkManagerWebsocket(AsyncWith, Protocol):
	async def send(self, data: Union[bytes, str]): ...
	async def receive(self, timeout: Optional[Union[int, float]] = None) \
			-> Union[bytes, str]: ...

class NetworkManagerResponse(AsyncWith, Protocol):
	async def body(self) -> bytes: ...

class GatewayManager(Protocol):
	async def heartbeat_now(self): ...
	async def heartbeat_set(self, interval: int): ...
	async def send(self, data: JSON): ...

class CacheManager(Protocol):
	async def cache_user(self, user: User): ...
	async def cache_guild(self, guild: Guild): ...

	def get_user(self, id: int) -> Optional[User]: ...
	def get_guild(self, id: int) -> Optional[Guild]: ...
	def get_channel(self, id: int) -> Optional[GuildChannel]: ...

	async def fetch_guild(self, id: int) -> Optional[Guild]: ...
