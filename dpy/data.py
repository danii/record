from __future__ import annotations
from typing_extensions import TypeAlias
from .ducks import JSON as _JSON, CacheManager
from abc import ABC, abstractmethod
from itertools import tee
from typing import Any, Callable, Generator, Generic, Literal, Optional, \
	TypeVar, Union, cast, overload

_T = TypeVar("_T")
_U = TypeVar("_U")
_constructorSelf = TypeVar("_constructorSelf", bound="_constructor[Any]")

CacheFetchFetcher: TypeAlias = \
	Callable[[CacheManager], Callable[[_U], Optional[_T]]]

class _constructor(ABC, Generic[_T]):
	"""The abstract base class for defining self constructing properties.

	Effectively a runtime controllable reference (one that can change where it
	points to without changing itself) with information on how to build said
	referenced data. The reference functionality is implemented with descriptors
	and a magic property that must be defined on holding objects.
	("__property_map__")
	"""

	@abstractmethod
	def construct(self, property: str, data: dict[str, _JSON],
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

	def construct(self, property: str, data: dict[str, _JSON],
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

class _list_constructor(_constructor[list[_T]]):
	"""Super constructor for lists."""

	_constructor_: _constructor[_T]

	def __init__(self, constructor: _constructor[_T]):
		self._constructor_ = constructor
		super().__init__()

	def construct(self, property: str, data: dict[str, _JSON],
			cache: Optional[CacheManager] = None) -> list[_T]:
		# Type checking...
		list_value: Union[list[Any], Any] = data[property]
		if not isinstance(list_value, list):
			raise TypeError(f"expected type list, found type {type(list_value)}")

		list_return: list[_T] = []
		# For each item in the list...
		for value in list_value:
			# ...run the constructor.
			construct = cast(_constructor[_T], self._constructor_).construct
			list_return.append(construct(property, {property: value}))
		return list_return

class _optional_constructor(_constructor[Optional[_T]]):
	"""Super constructor for optional data."""

	_constructor_: _constructor[_T]

	def __init__(self, constructor: _constructor[_T]):
		self._constructor_ = constructor
		super().__init__()

	def construct(self, property: str, data: dict[str, _JSON],
			cache: Optional[CacheManager] = None) -> Optional[_T]:
		# If data exists...
		if property in data:
			# ...then run the constructor.
			construct = cast(_constructor[_T], self._constructor_).construct
			return construct(property, data, cache)
		else:
			# Otherwise return None.
			return None

class _convert_constructor(_constructor[_T], Generic[_U, _T]):
	"""Super constructor for converting data before storing."""

	_constructor_: _constructor[_U]
	_convert: Callable[[_U], _T]

	def __init__(self, constructor: _constructor[_U],
			convert: Callable[[_U], _T]):
		self._constructor_ = constructor
		self._convert = convert
		super().__init__()

	def construct(self, property: str, data: dict[str, _JSON],
			cache: Optional[CacheManager] = None) -> _T:
		# Convert the data with _convert.
		construct = cast(_constructor[_T], self._constructor_).construct
		return self._convert(construct(property, data, cache))

class _entity_reference(_constructor[Union[_T, _U]], Generic[_T, _U]):
	"""Super constructor for references of things in cache."""

	_id_constructor: _constructor[_U]
	_entity: type[_T]
	_fetch: Union[str, CacheFetchFetcher[_U, _T]]

	def __init__(self, reference_to: type[_T],
			fetch: Union[str, CacheFetchFetcher[_U, _T]], *,
			id: _constructor[_U] = _convert_constructor(_auto(str), int)):
		self._id_constructor = id
		self._entity = reference_to
		self._fetch = fetch
		super().__init__()

	def construct(self, property: str, data: dict[str, _JSON],
			cache: Optional[CacheManager] = None) -> Union[_T, _U]:
		# Get the identifier.
		construct = cast(_constructor[_U], self._id_constructor).construct
		identifier = construct(property, data, cache)

		# If cache is none...
		if cache is None:
			# ...just return the identifier.
			return identifier
		else:
			# Otherwise use the cache with the identifier to get the desired data.
			fetcher = getattr(cache, self._fetch) if isinstance(self._fetch, str) \
				else self._fetch(cache)
			value = fetcher(data[property])

			# Type check.
			if value is not None and not isinstance(value, self._entity):
				raise TypeError(f"expected type {self._entity}, \
found type {type(value)}")
			return identifier if value is None else value

class _as(_constructor[_T]):
	"""Super constructor for fetching data under a different property name."""

	_constructor_: _constructor[_T]
	_as: str

	def __init__(self, constructor: _constructor[_T], as_: str):
		self._constructor_ = constructor
		self._as = as_
		super().__init__()

	def construct(self, property: str, data: dict[str, _JSON],
			cache: Optional[CacheManager] = None) -> _T:
		# Delegate using the desired name.
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

	def __init__(self, data: dict[str, _JSON], cache: Optional[CacheManager]=None):
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
	id = _id_constructor
	content = _auto(str)

	def __str__(self) -> str:
		return self.content

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
