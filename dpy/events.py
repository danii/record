from .data import *
from dataclasses import dataclass

class Event:
	pass

@dataclass
class ReadyEvent(Event):
	user: SelfUser
	guilds: list[Guild]

@dataclass
class GuildCreateEvent(Event):
	guild: AvailableGuild

@dataclass
class MessageCreateEvent(Event):
	message: Message
