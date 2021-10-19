from __future__ import annotations
from .ducks import CacheManager
from abc import ABC, abstractclassmethod
from typing import Any, Optional, Union

def entity(cls: type):
	keys = cls.__dict__
	annotations = cls.__annotations__.keys()
	properties = [key for key in annotations if key not in keys]

	def __init__(self: cls, key = None, /, **keywords):
		super(cls, self).__init__(key, **keywords)
		for key in properties:
			the = key[:]
			setattr(self, f"_{the}", keywords[the])
	setattr(cls, "__init__", __init__)

	for key in properties:
		def get_getter(key):
			def getter(self: cls):
				return getattr(self, f"_{key}")
			return getter
		setattr(cls, key, property(get_getter(key)))

	return cls

class Entity(ABC):
	_INSTANTIATION_NONCE = object()

	def __init__(self, key = None, /, **_):
		if key != self._INSTANTIATION_NONCE:
			raise TypeError("entities cannot be created manually")

	@abstractclassmethod
	def _from_api(cls, cache: Optional[CacheManager], data: Any): ...

@entity
class SelfUser(Entity):
	id: int
	username: str

	@classmethod
	def _from_api(cls, cache: Optional[CacheManager], data):
		return cls(cls._INSTANTIATION_NONCE, id=data["id"],
			username=data["username"])

@entity
class Guild(Entity):
	id: int

	@property
	def available(self):
		return False

	def __repr__(self) -> str:
		return "UnavailableGuild"

	@classmethod
	def _from_api(cls, cache: Optional[CacheManager], data):
		return cls(cls._INSTANTIATION_NONCE, id=data["id"])

@entity
class AvailableGuild(Guild):
	name: str
	roles: list[Role]
	channels: list[GuildChannel]

	@property
	def available(self):
		return True

	def __repr__(self) -> str:
		return self.name

	@classmethod
	def _from_api(cls, cache: Optional[CacheManager], data):
		roles = [Role._from_api(cache, role) for role in data["roles"]]
		channels = [GuildChannel._from_api(cache, channel) \
			for channel in data["channels"]]

		return cls(cls._INSTANTIATION_NONCE, id=data["id"], name=data["name"],
			roles=roles, channels=channels)

@entity
class Role(Entity):
	id: int
	name: str

	def __str__(self) -> str:
		return f"<@&{self.id}>"

	def __repr__(self) -> str:
		return self.name

	@classmethod
	def _from_api(cls, cache: Optional[CacheManager], data):
		return cls(cls._INSTANTIATION_NONCE, id=data["id"], name=data["name"])

@entity
class GuildChannel(Entity):
	id: int
	name: str

	def __repr__(self) -> str:
		return self.name

	@classmethod
	def _from_api(cls, cache: Optional[CacheManager], data):
		type = data["type"]

		if type == 0:
			return GuildTextChannel._from_api(cache, data)
		elif type == 4:
			return GuildCategoryChannel._from_api(cache, data)

@entity
class GuildCategoryChannel(GuildChannel):
	@classmethod
	def _from_api(cls, cache: Optional[CacheManager], data):
		return cls(cls._INSTANTIATION_NONCE, id=data["id"], name=data["name"])

@entity
class GuildChildChannel(GuildChannel):
	parent: Optional[Union[GuildCategoryChannel, int]]

@entity
class GuildTextChannel(GuildChildChannel):
	topic: str
	nsfw: bool

	def __str__(self) -> str:
		return f"<@#{self.id}>"

	@classmethod
	def _from_api(cls, cache: Optional[CacheManager], data):
		parent = data["parent_id"] if cache is None else \
			cache.get_channel(data["parent_id"])

		return cls(cls._INSTANTIATION_NONCE, id=data["id"], name=data["name"],
			topic=data["topic"], nsfw=data.get("nsfw", False), parent=parent)


@entity
class Message(Entity):
	id: int
	content: str
