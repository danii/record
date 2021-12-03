from __future__ import annotations
from typing_extensions import TypeAlias
from .ducks import CacheManager
from abc import ABC, abstractmethod
from itertools import tee
from typing import Any, Callable, Generator, Generic, Literal, Optional, \
	TypeVar, Union, cast, overload

_T = TypeVar("_T")
_I = TypeVar("_I")
_constructorSelf = TypeVar("_constructorSelf", bound="_constructor[Any]")

CacheFetchFetcher: TypeAlias = \
	Callable[[CacheManager], Callable[[_I], Optional[_T]]]

class _constructor(ABC, Generic[_T]):
	"""The abstract base class for defining self constructing properties.

	Effectively a runtime controllable reference (one that can change where it
	points to without changing itself) with information on how to build said
	referenced data. The reference functionality is implemented with descriptors
	and a magic property that must be defined on holding objects.
	("__property_map__")
	"""

	@abstractmethod
	def construct(self, property: str, data: dict[str, Any],
			cache: Optional[CacheManager] = None) -> _T:
		"""Constructs the referenced data."""

	@overload
	def __get__(self: _constructorSelf, instance: None, owner: type) \
			-> _constructorSelf: ...
	@overload
	def __get__(self, instance: Any, owner: type) -> _T: ...
	def __get__(self: _constructorSelf, instance: Optional[Any], owner: type) \
			-> Union[_constructorSelf, _T]:
		"""Accesses the referenced data."""

		if instance is None:
			return self

		property_map = getattr(instance, "__property_map__", None)
		if property_map is None:
			raise AttributeError("constructor cannot be used on values that do not have a __property_map__ field")
		return property_map[self]()

class _auto(_constructor[_T]):
	"""Automagic constructor of inplace data.

	Constructed data is type checked, and if the specified type is a decendant of
	Entity, constructed.
	"""

	_Type: type[_T]

	def __init__(self, Type: type[_T]):
		self._Type = Type
		super().__init__()

	def construct(self, property: str, data: dict[str, Any],
			cache: Optional[CacheManager] = None) -> Optional[_T]:
		# If the specified type is a decendant of Entity...
		if Entity in self._Type.mro():
			# ...build the type.
			return self._Type(data[property], cache)
		else:
			# Otherwise type check and return.
			value = data.get(property, None)
			if not isinstance(value, self._Type):
				raise TypeError(f"expected type {self._Type}, found type {type(value)}")
			return value

class _list_constructor(_constructor[_T]):
	_constructor_: _constructor[_T]

	def __init__(self, constructor: _constructor[_T]):
		self._constructor_ = constructor
		super().__init__()

	def construct(self, property: str, data: dict[str, Any],
			cache: Optional[CacheManager] = None) -> list[_T]:
		list_value: Union[list[Any], Any] = data[property]
		if not isinstance(list_value, list):
			raise TypeError()

		list_return: list[_T] = []
		for value in list_value:
			construct = cast(_constructor[_T], self._constructor_).construct
			list_return.append(construct(property, {property: value}))
		return list_return

class _optional_constructor(_constructor[Optional[_T]]):
	_constructor_: _constructor[_T]

	def __init__(self, constructor: _constructor[_T]):
		self._constructor_ = constructor
		super().__init__()

	def construct(self, property: str, data: dict[str, Any],
			cache: Optional[CacheManager] = None) -> Optional[_T]:
		if property in data:
			construct = cast(_constructor[_T], self._constructor_).construct
			return construct(property, data, cache)
		else:
			return None

class _convert_constructor(_constructor[_T], Generic[_I, _T]):
	_constructor_: _constructor[_I]
	_convert: Callable[[_I], _T]

	def __init__(self, constructor: _constructor[_I],
			convert: Callable[[_I], _T]):
		self._constructor_ = constructor
		self._convert = convert
		super().__init__()

	def construct(self, property: str, data: dict[str, Any],
			cache: Optional[CacheManager] = None) -> _T:
		construct = cast(_constructor[_T], self._constructor_).construct
		return self._convert(construct(property, data, cache))

class _entity_reference(_constructor[Union[_T, _I]], Generic[_T, _I]):
	def __init__(self, reference_to: type[_T],
			fetch: Union[str, CacheFetchFetcher[_I, _T]], *,
			id: _constructor[_I] = _convert_constructor(_auto(str), int)):
		self._entity = reference_to
		self._fetch = fetch
		super().__init__()

	def construct(self, property: str, data: dict[str, Any],
			cache: Optional[CacheManager] = None) -> _T:
		if cache is None:
			return data[property]
		else:
			fetcher = getattr(cache, self._fetch) if isinstance(self._fetch, str) \
				else self._fetch(cache)
			result = fetcher(data[property])

			if result is not None and not isinstance(result, self._entity):
				raise TypeError("expected entity")
			return data[property] if result is None else result

class _as(_constructor[_T]):
	def __init__(self, constructor: _constructor[_T], as_: str):
		self._constructor_ = constructor
		self._as = as_
		super().__init__()

	def construct(self, property: str, data: dict[str, Any],
			cache: Optional[CacheManager] = None) -> _T:
		construct = cast(_constructor[_T], self._constructor_).construct
		return construct(self._as, data, cache)

class Entity:
	"""An advanced tuple that can be built from raw JSON data.

	All of an entities properties are "constructors", dynamic references which
	encode information on how to build the data they point to. Regardless of this
	systems complexity, it allows for easy creation of advanced data classes.
	"""

	__slots__ = "__property_map__", "_tuple"
	__property_map__: dict[_constructor[Any], Callable[[], Any]]
	_tuple: tuple[Any, ...]

	def __init__(self, data: dict[str, Any], cache: Optional[CacheManager]=None):
		def generate():
			cls = type(self)
			constructors = cast( # Python type checkers are dumb as ****.
				Generator[tuple[str, _constructor[int]], None, None],
				(
					(key, property) for key in dir(cls)
						if isinstance(property := getattr(cls, key), _constructor)
				)
			)

			def get_getter(index: int):
				return lambda: self._tuple[index]

			for index, (key, property) in enumerate(constructors):
				try:
					value = property.construct(key, data, cache)
				except Exception as exception:
					raise ValueError(f"error occurred while constructing property \
\"{key}\" of {type(self)}") from exception

				yield (property, get_getter(index)), value

		dict_generator, tuple_generator = tee(generate())
		self.__property_map__ = dict(tuple for tuple, _ in dict_generator)
		self._tuple = tuple(data for _, data in tuple_generator)

_id_constructor = _convert_constructor(_auto(str), int)

class User(Entity):
	id = _id_constructor
	username = _auto(str)

class SelfUser(User):
	pass

class Role(Entity):
	id = _id_constructor
	name = _auto(str)

	def __str__(self) -> str:
		return f"<@&{self.id}>"

	def __repr__(self) -> str:
		return self.name

class Channel(Entity):
	id = _id_constructor

class TextChannel(Channel):
	pass

class GuildChannel(Channel):
	name = _auto(str)

	def __repr__(self) -> str:
		return self.name

class GuildCategoryChannel(GuildChannel):
	pass

class GuildChildChannel(GuildChannel):
	parent = _optional_constructor(_entity_reference(GuildCategoryChannel, lambda c: c.get_channel)) #Optional[Union[GuildCategoryChannel, int]]

class GuildTextChannel(GuildChildChannel, TextChannel):
	topic = _auto(str)
	nsfw = _auto(bool)

	def __str__(self) -> str:
		return f"<@#{self.id}>"

class Message(Entity):
	id = _auto(int)
	content = _auto(str)

class Guild(Entity):
	id = _id_constructor

	@property
	def available(self) -> bool:
		return False

	def __repr__(self) -> str:
		return "UnavailableGuild"

class AvailableGuild(Guild):
	name = _auto(str)
	owner = _as(_entity_reference(User, lambda c: c.get_user), "owner_id")

	roles = _list_constructor(_auto(Role))
	channels = _list_constructor(_auto(GuildChannel))

	@property
	def available(self) -> Literal[True]:
		return True

	def __repr__(self) -> str:
		return self.name
