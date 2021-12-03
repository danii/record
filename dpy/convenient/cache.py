from __future__ import annotations

class DefaultCache:
	def __init__(self):
		pass

	async def cache_user(self, user): ...
	async def cache_guild(self, user): ...

	def get_user(self, id: int): ...
	def get_guild(self, id: int): ...
	def get_channel(self, id: int): ...

	async def fetch_guild(self, id: int): ...
