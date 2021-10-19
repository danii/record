from abc import ABC, abstractclassmethod
from typing import Any

def entity(cls: type):
	keys = cls.__dict__
	annotations = cls.__annotations__.keys()
	properties = [key for key in annotations if key not in keys]

	def __init__(self: cls, key = None, /, **keywords):
		super(cls, self).__init__(key)
		for key in properties:
			setattr(self, f"_{key}", keywords[key])
	setattr(cls, "__init__", __init__)

	for key in properties:
		def getter(self: cls):
			return getattr(self, f"_{key}")
		setattr(cls, key, property(getter))

	return cls

class Entity(ABC):
	_INSTANTIATION_NONCE = object()

	def __init__(self, key = None, /):
		if key != self._INSTANTIATION_NONCE:
			raise TypeError("entities cannot be created manually")

	@abstractclassmethod
	def _from_api(cls, data: Any): ...

@entity
class SelfUser(Entity):
	id: int
	username: str

	@classmethod
	def _from_api(cls, data):
		return cls(cls._INSTANTIATION_NONCE, id=data["id"],
			username=data["username"])

@entity
class Guild(Entity):
	id: int

	@property
	def available(self):
		return False

	@classmethod
	def _from_api(cls, data):
		return cls(cls._INSTANTIATION_NONCE, id=data["id"])

@entity
class AvailableGuild(Guild):
	id: int
	name: str

	@property
	def available(self):
		return True
