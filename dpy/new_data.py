from __future__ import annotations
from abc import ABC, abstractmethod
from itertools import count
from typing import Any, Optional

def bounded_property(internal: str, start: int, end: int):
	def getter(self):
		return getattr(self, internal)

	return bounded_setter(internal, start, end)(getter)

def bounded_setter(internal: str, start: int, end: int):
	def bounded_setter_decorator(function):
		name = function.__name__

		def setter(self, value):
			if len(value) < start or len(value) > end:
				raise ValueError(f'property "{name}" must be between {start} and {end} characters, but it was {len(value)} characters')
			setattr(self, internal, value)

		return property(function, setter)
	return bounded_setter_decorator

class NewGuild:
	_name: Optional[str]
	_roles: list[NewRole]
	_channels: list[NewGuildChannel]

	name = bounded_property("_name", 2, 100)
	roles = bounded_property("_roles", 0, 250)
	channels = bounded_property("_channels", 0, 250)

	#verification_level: Optional[int] # TODO: Verification Level
	#default_message_notifications: Optional[int]
	#explicit_content_filter: Optional[int]


	def __init__(self):
		self._name = None
		self._roles = []
		self._channels = []

	def _to_api(self) -> dict[str, Any]:
		if self._name is None:
			raise ValueError(f'property "name" must be set')

		return {
			"name": self._name,
			"roles": [role._to_api(count()) for role in self._roles],
			"channels": [channel._to_api(count()) for channel in self._channels]
		}

class NewRole:
	_id: Optional[int]
	_name: Optional[str]
	_color: Optional[int]

	name = bounded_property("_name", 0, 100)

	position: int
	hoist: bool
	mentionable: bool

	def __init__(self):
		self._id = None
		self._name = None

	def _to_api(self, counter: count) -> dict[str, Any]:
		if self._name is None:
			raise ValueError(f'property "name" must be set')

		if self._id is None:
			self._id = next(counter)

		return {
			"id": self._id,
			"name": self._name,
			"color": 0,
			"hoist": self.hoist,
			"position": self._id,
			"mentionable": self.mentionable
		}

class NewGuildChannel(ABC):
	_id: Optional[int]
	_name: Optional[str]

	def __init__(self):
		self._id = None
		self._name = None

	@abstractmethod
	def _to_api(self, counter: count) -> dict[str, Any]: ...

	@bounded_setter("_name", 1, 100)
	def name(self) -> Optional[str]:
		return None if self._name is None else \
			self._name_implicit_transform(self._name)

	@staticmethod
	def _name_implicit_transform(name: str) -> str:
		return name

class NewGuildCategoryChannel(NewGuildChannel):
	def _to_api(self, counter: count) -> dict[str, Any]:
		if self._name is None:
			raise ValueError(f'property "name" must be set')

		if self._id is None:
			self._id = next(counter)

		return {
			"id": self._id,
			"type": 4,
			"name": self.name
		}

class NewGuildChildChannel(NewGuildChannel):
	parent: Optional[NewGuildCategoryChannel]

class NewGuildTextChannel(NewGuildChildChannel):
	_topic: Optional[str]

	topic = bounded_property("_topic", 0, 1024)

	nsfw: bool

	def __init__(self):
		super().__init__()
		self._topic = None

	def _to_api(self, counter: count) -> dict[str, Any]:
		if self._name is None:
			raise ValueError(f'property "name" must be set')

		if self._id is None:
			self._id = next(counter)

		return {
			"id": self._id,
			"type": 0,
			"name": self.name,
			"topic": self._topic
		}

	@staticmethod
	def _name_implicit_transform(name: str) -> str:
		return name.lower().replace(" ", "-").replace("_", "-")
