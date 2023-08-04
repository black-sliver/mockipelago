from typing import cast, Any, Dict, List, Tuple

from server import MockServer
from mock import Event, On, Do, Trigger, Action

# player: location: (item, receiver, flags)
locations: Dict[int, Dict[int, Tuple[int, int, int]]] = {
    1: {
        4503599627370494: (4503599627370495, 1, 0),
        4503599627370495: (4503599627370494, 1, 0),
    },
}

# player: (name, game)
slot_info: Dict[int, Tuple[str, str]] = {
    1: ("Player", "Test")
}

# player: json
slot_data: Dict[int, Dict[str, Any]] = {
    1: {"some_integer": 4503599627370495}
}

events: List[Event] = [
    {
        "trigger": Trigger(on=On.CONNECT, player=1),
        "action": Action(do=Do.CHECK, player=1, location=4503599627370495),
        "delay": 0.1,
    },
    {
        "trigger": Trigger(on=On.CONNECT, player=1),
        "action": Action(do=Do.STOP),
        "delay": 1,
    },
]

server = MockServer({
    "locations": locations,
    "slot_info": slot_info,
    "slot_data": slot_data
}, events=cast(List[Event], events))
server.check_sync(1, 4503599627370494)  # pre-collect

if __name__ == "__main__":
    server.run()
