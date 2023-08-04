"""
Very incomplete WIP Archipelago mock / dummy server.
There is currently no main. You have to import this file, see sample.py
"""

import asyncio
import json
from typing import Any, Dict, List, NamedTuple, Set

import websockets

import mock
from netutils import encode


class NetworkItem(NamedTuple):
    item: int
    location: int
    player: int
    flags: int = 0


class NetworkPlayer(NamedTuple):
    team: int
    slot: int
    alias: str
    name: str


class NetworkSlot(NamedTuple):
    name: str
    game: str
    type: int = 1
    group_members: List[int] = []


class Client(NamedTuple):
    player: int
    connection: Any

    async def send(self, data):
        message = encode(data)
        print(f"< {message}")
        await self.connection.send(message)


class Server:
    _locations: Dict[int, Dict[int, NetworkItem]]
    _slot_info: Dict[int, NetworkSlot]
    _slot_data: Dict[int, Any]
    _connect_names: Dict[str, int]
    _clients: List[Client]
    _checked: Dict[int, Set[int]]  # no team support yet
    _items: Dict[int, List[NetworkItem]]  # all remote, no items_handling yet
    _stop: asyncio.Event

    def __init__(self, data: Dict[str, Any]) -> None:
        # multi data
        self._locations = {player: {
            location: NetworkItem(item, location, player, flags) for location, (item, player, flags) in player_locations.items()
        } for player, player_locations in data["locations"].items()}
        self._slot_info = {1: NetworkSlot("Player", "Game")}
        self._slot_data = {1: {}}
        # internal cache
        self._connect_names = {info.name: number for number, info in self._slot_info.items()}
        # state
        self._clients = []
        self._checked = {number: set() for number in self._slot_info}
        self._items = {number: [] for number in self._slot_info}
        self._stop = asyncio.Event()

    async def stop(self):
        """Stop the server"""
        self._stop.set()

    async def check(self, player: int, location: int) -> None:
        """Collect a location and send item"""
        if location not in self._checked[player]:
            item = self._locations[player][location]
            await self._send_location(player, location)
            await self._send_item(player, item.player, item)

    def check_sync(self, player: int, location: int) -> None:
        if location not in self._checked[player]:
            item = self._locations[player][location]
            self._checked[player].add(location)
            self._items[item.player].append(NetworkItem(item.item, item.location, player, item.flags))

    async def _send_item(self, sender: int, receiver: int, item: NetworkItem) -> None:
        """Send an item"""
        item = NetworkItem(item.item, item.location, sender, item.flags)
        self._items[receiver].append(item)
        await self._send_to_player(receiver, [{
            "cmd": "ReceivedItems",
            "index": len(self._items[receiver]) - 1,
            "items": [item]
        }])

    async def _send_location(self, player: int, location: int) -> None:
        """Send room update for location"""
        if location not in self._checked[player]:
            self._checked[player].add(location)
            await self._send_to_player(player, [{
                "cmd": "RoomUpdate",
                "checked_locations": [location]
            }])

    async def _send_to_player(self, receiver: int, data: List[Dict[str, Any]]) -> None:
        for client in self._clients:
            if client.player == receiver:
                await client.send(data)

    async def _on_cmd_connect(self, connection, data: Dict[str, Any]) -> None:
        # TODO: auth player
        for i, client in enumerate(self._clients):
            if client.connection is connection:
                self._clients.pop(i)
                break
        client = Client(self._connect_names[data["name"]], connection)
        setattr(connection, "client", client)  # back-ref
        self._clients.append(client)
        await client.send([{
            "cmd": "Connected",
            "team": 0,
            "slot": client.player,
            "players": [NetworkPlayer(0, player, "", self._slot_info[player].name) for player in self._locations],
            "missing_locations": sorted(set(self._locations[client.player]) - self._checked[client.player]),
            "checked_locations": self._checked[client.player],
            "slot_data": self._slot_data[client.player],
            "slot_info": self._slot_info,
            "hint_points": 0,  # not implemented
        }])

    async def _on_open(self, connection) -> None:
        # TODO: send room info
        try:
            while True:
                message = await connection.recv()
                print(f"> {message}")
                for data in json.loads(message):
                    await getattr(self, f"_on_cmd_{data['cmd'].lower()}")(connection, data)
        except websockets.ConnectionClosedOK:
            pass
        finally:
            for i, client in enumerate(self._clients):
                if client.connection is connection:
                    self._clients.pop(i)
                    break

    async def serve(self):
        async with websockets.serve(self._on_open, "localhost", 38281):
            await self._stop.wait()

    def run(self) -> None:
        asyncio.run(self.serve())


class MockServer(Server):
    _events: List[mock.Event]
    _tasks: List[asyncio.Task]

    def __init__(self, data: Dict[str, Any], events: List[mock.Event]) -> None:
        super().__init__(data)
        self._events = events
        self._tasks = []

    async def _mock_action(self, action, delay):
        if delay and delay > 0:
            async def delayed():
                await asyncio.sleep(delay)
                await self._mock_action(action, 0)
            self._tasks.append(asyncio.create_task(delayed()))
            return
        if action["do"] == mock.Do.STOP:
            await self.stop()
        elif action["do"] == mock.Do.CHECK:
            await self.check(action["player"], action["location"])

    async def _on_cmd_connect(self, connection, data: Dict[str, Any]) -> None:
        await super()._on_cmd_connect(connection, data)
        client = getattr(connection, "client")
        for event in self._events:
            if event["trigger"]["on"] == mock.On.CONNECT and client.player == event["trigger"]["player"]:
                await self._mock_action(event["action"], event["delay"])
