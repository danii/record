from __future__ import annotations
from collections import defaultdict

from inspect import iscoroutine
from ..gateway.events import *
from typing import Awaitable, Callable

def manufacture_registerer(event: type[Event]):
	def registerer(self: Dispatcher, function: Callable[..., Awaitable]):
		self._listeners[event].append(function)
		return function
	return registerer

class Dispatcher:
	_listeners: defaultdict[type[Event], list[Callable[..., Awaitable]]]

	def __init__(self):
		self._listeners = defaultdict(list)

	async def dispatch(self, event: Event):
		for listener in self._listeners[type(event)]:
			result = listener(event)
			if iscoroutine(result):
				await result

	on_ready = manufacture_registerer(ReadyEvent)
	on_guild_create = manufacture_registerer(GuildCreateEvent)
	on_message_create = manufacture_registerer(MessageCreateEvent)
