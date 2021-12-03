from __future__ import annotations

from .events import *
from ..data import *
from ..ducks import JSON, CacheManager, GatewayManager, type_check
from typing import Awaitable, Callable, Optional

async def process_payload(payload: JSON, token: str, *,
		dispatch: Callable[[Event], Awaitable[None]], manager: GatewayManager,
		cache: Optional[CacheManager] = None):
	if not isinstance(payload, dict):
		raise TypeError(f"expected type dict, found type {type(payload)}")

	op_code = type_check(payload["op"], int)
	data = payload["d"]

	if op_code == 0: # Dispatch
		data = type_check(data, dict[str, JSON])
		event = type_check(payload["t"], str)

		if event == "READY":
			user = SelfUser(type_check(data["user"], dict[str, JSON]), cache)
			guilds = [
				Guild(type_check(guild, dict[str, JSON]), cache) \
					for guild in type_check(data["guilds"], list[JSON])
			]

			if cache is not None:
				for guild in guilds:
					await cache.cache_guild(guild)
				await cache.cache_user(user)

			await dispatch(ReadyEvent(user, guilds))
		elif event == "GUILD_CREATE":
			guild = AvailableGuild(data, cache)

			if cache is not None:
				await cache.cache_guild(guild)

			await dispatch(GuildCreateEvent(guild))
		elif event == "MESSAGE_CREATE":
			message = Message(data, cache)

			# TODO: CACHE

			await dispatch(MessageCreateEvent(message))
	elif op_code == 1:
		await manager.heartbeat_now()
	elif op_code == 10: # Hello
		data = type_check(data, dict[str, JSON])
		await manager.heartbeat_set(type_check(data["heartbeat_interval"], int))

		await manager.send({
			"op": 2,
			"d": {
				"token": token,
				"properties": {
					"$os": "linux",
					"$browser": "an unnamed in-dev Discord library",
					"$device": "an unnamed in-dev Discord library"
				},
				"compress": False,
				"intents": 0b111111111111111
			}
		})
