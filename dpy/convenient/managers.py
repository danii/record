from types import TracebackType
from aiohttp.client_reqrep import ClientResponse
from aiohttp.client_ws import ClientWebSocketResponse
from ..ducks import NetworkManager, NetworkManagerResponse, NetworkManagerWebsocket
from aiohttp import ClientSession
from asyncio import TimeoutError as AsyncIOTimeoutError
from typing import Optional, TypeVar, Union, cast

_E = TypeVar("_E", bound=BaseException)

class AIOHTTPNetworkManager:
	session: ClientSession

	def __init__(self, session: Optional[ClientSession] = None):
		self.session = ClientSession() if session is None else session

	async def __aenter__(self):
		await self.session.__aenter__()
		return self

	async def __aexit__(self, exception_type: type[_E], exception: _E,
			traceback: TracebackType):
		await self.session.__aexit__(exception_type, exception, traceback)

	async def request(self, url: str, *, method: str = "GET",
			data: Optional[Union[str, bytes]] = None, headers: dict[str, str] = {}):
		response = await self.session.request(method, url,
			headers=headers, data=data)
		return AIOHTTPNetworkManagerResponse(response)

	async def request_websocket(self, url: str):
		socket = await self.session.ws_connect(url)
		return AIOHTTPNetworkManagerWebsocket(socket)

_: type[NetworkManager] = AIOHTTPNetworkManager

class AIOHTTPNetworkManagerResponse:
	response: ClientResponse

	def __init__(self, response: ClientResponse):
		self.response = response

	async def __aenter__(self):
		await self.response.__aenter__()
		return self

	async def __aexit__(self, exception_type: type[_E], exception: _E,
			traceback: TracebackType):
		await self.response.__aexit__(exception_type, exception, traceback)

	async def body(self) -> bytes:
		return await self.response.read()

__: type[NetworkManagerResponse] = AIOHTTPNetworkManagerResponse

class AIOHTTPNetworkManagerWebsocket:
	socket: ClientWebSocketResponse

	def __init__(self, socket: ClientWebSocketResponse):
		self.socket = socket

	async def __aenter__(self):
		#await self.socket.__aenter__()
		return self

	async def __aexit__(self, exception_type: type[_E], exception: _E,
			traceback: TracebackType):
		#await self.socket.__aexit__(exception_type, exception, traceback)
		pass

	async def send(self, data: Union[bytes, str]):
		if isinstance(data, str):
			await self.socket.send_str(data)
		else:
			await self.socket.send_bytes(data)

	async def receive(self, timeout: Optional[Union[int, float]] = None) \
			-> Union[bytes, str]:
		try:
			response = await self.socket.receive(timeout=timeout)
			return cast(Union[bytes, str], getattr(response, "data"))
		except AsyncIOTimeoutError as exception:
			raise TimeoutError() from exception

___: type[NetworkManagerWebsocket] = AIOHTTPNetworkManagerWebsocket
