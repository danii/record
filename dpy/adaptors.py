from . import GatewayClient
from aiohttp.client_ws import ClientWebSocketResponse
from json import loads

class AIOHTTPGatewayManager:
	socket: ClientWebSocketResponse
	client: GatewayClient

	def __init__(self, socket: ClientWebSocketResponse, *arguments):
		self.socket = socket
		self.client = GatewayClient(self, *arguments)

	async def send_str(self, data: str):
		await self.socket.send_str(data)

	async def run(self):
		while True:
			data = loads(await self.socket.receive_str())
			#print(data)
			await self.client.process_payload(data)
