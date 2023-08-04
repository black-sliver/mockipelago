from enum import Enum
from typing import TypedDict, NotRequired


class On(Enum):
    CONNECT = "connect"


class Do(Enum):
    CHECK = "check"
    STOP = "stop"


class Trigger(TypedDict):
    on: On
    player: int


class Action(TypedDict):
    do: Do
    player: NotRequired[int]
    location: NotRequired[int]


class Event(TypedDict):
    trigger: Trigger
    action: Action
    delay: float
