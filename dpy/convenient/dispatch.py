from __future__ import annotations
from ..gateway.events import *
from collections import defaultdict
from inspect import iscoroutine
from typing import Awaitable, Callable, TypeVar

_E = TypeVar("_E", bound=Event, contravariant=True)

def manufacture_registerer(event: type[_E]):
	def registerer(self: BasicDispatcher,
			function: Callable[[_E], Union[Awaitable[None], None]]):
		self._listeners[event].append(function)
		return function
	return registerer

class BasicDispatcher:
	_listeners: defaultdict[
		type[Event],
		list[Callable[[Event], Union[Awaitable[None], None]]]
	]

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
