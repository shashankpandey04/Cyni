import discord
import asyncio
import roblox
import datetime
from discord.ext import commands
import json
from utils.constants import YELLOW_COLOR
from utils.utils import discord_time
from bson import ObjectId
import aiohttp
import typing


class ServerLinkNotFound(commands.CheckFailure):
    pass

class ResponseFailed(Exception):
    detail: str | None
    code: int | None
    data: str

    def __init__(self, data: str, detail: str | None = None, code: int | None = None, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return f"ResponseFailed(data={self.data}, detail={self.detail}, code={self.code})"

class ServerStatus():
    name: str | None
    owner_id: int | None
    co_owner_ids: list[int] | None
    current_players: int | None
    max_players: int | None
    join_key: str | None
    verification: str
    team_balance: bool

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerPlayers():
    player: str | None
    permission: str
    call_sign: str | None
    team: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerJoinLogs():
    join: bool
    timestamp: int
    player: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerQueue():
    total_players: int

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerKillLogs():
    killed: str | None
    timestamp: int
    killer: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerCommandLogs():
    player: str | None
    timestamp: int
    command: str | None


class ServerModCalls():
    caller: str | None
    moderator: str | None
    timestamp: int

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerBans():
    player_id: int

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerVehicles():
    texture: str | None
    name: str | None
    owner: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerCommand():
    command: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class PRC_API_Client:
    def __init__(self,bot,base_url: str, api_key: str):
        self.bot = bot
        self.base_url = base_url
        self.api_key = api_key
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()


    async def fetch_server_key(self, server_id: int):
        return await self.bot.erlc_keys.find_by_id(server_id)

    async def _send_request(self, method: typing.Literal["GET", "POST"], endpoint: str, server_id: int, data: dict = None, key: str = None):
        if key is None:
            raise ServerLinkNotFound("Server link not found.")
        
        async with self.session.request(method, f"{self.base_url}{endpoint}", headers={
            "Authorization": self.api_key,
            "User-Agent": "Application",
            "Server-Key": key
        }, json=data) as resp:
            if resp.status != 200:
                data = await resp.json()
                raise ResponseFailed(data=data, detail=data.get("detail"), code=resp.status)
            return await resp.json()
            

    async def get_server_status(self, server_id: int):
        status_code, response_json = await self._send_request('GET', '/server', server_id)
        if status_code == 200:
            return ServerStatus(
                name=response_json.get('name'),
                owner_id=response_json.get('owner_id'),
                co_owner_ids=response_json.get('co_owner_ids'),
                current_players=response_json.get('current_players'),
                max_players=response_json.get('max_players'),
                join_key=response_json.get('join_key'),
                verification=response_json.get('verification'),
                team_balance=response_json.get('team_balance')
            )
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )
        
    async def send_test_request(self, server_key: str) -> int | ServerStatus:
        code, response_json = await self._send_request('GET', '/server', 0, None, server_key)
        return code if code != 200 else ServerStatus(
            name=response_json.get('name'),
            owner_id=response_json.get('owner_id'),
            co_owner_ids=response_json.get('co_owner_ids'),
            current_players=response_json.get('current_players'),
            max_players=response_json.get('max_players'),
            join_key=response_json.get('join_key'),
            verification=response_json.get('verification'),
            team_balance=response_json.get('team_balance')
        )
        
    async def get_server_players(self, server_id: int):
        status_code, response_json = await self._send_request('GET', '/server/players', server_id)
        if status_code == 200:
            return [ServerPlayers(
                player=player.get('player'),
                permission=player.get('permission'),
                call_sign=player.get('call_sign'),
                team=player.get('team')
            ) for player in response_json]
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )
        
    async def get_server_join_logs(self, server_id: int):
        status_code, response_json = await self._send_request('GET', '/server/join_logs', server_id)
        if status_code == 200:
            return [ServerJoinLogs(
                join=log.get('join'),
                timestamp=log.get('timestamp'),
                player=log.get('player')
            ) for log in response_json]
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )
        
    async def get_server_queue(self, server_id: int):
        status_code, response_json = await self._send_request('GET', '/server/queue', server_id)
        if status_code == 200:
            return ServerQueue(
                total_players=response_json.get('total_players')
            )
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )
        
    async def get_server_kill_logs(self, server_id: int):
        status_code, response_json = await self._send_request('GET', '/server/kill_logs', server_id)
        if status_code == 200:
            return [ServerKillLogs(
                killed=log.get('killed'),
                timestamp=log.get('timestamp'),
                killer=log.get('killer')
            ) for log in response_json]
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )
        
    async def get_server_command_logs(self, server_id: int):
        status_code, response_json = await self._send_request('GET', '/server/command_logs', server_id)
        if status_code == 200:
            return [ServerCommandLogs(
                player=log.get('player'),
                timestamp=log.get('timestamp'),
                command=log.get('command')
            ) for log in response_json]
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )
        
    async def get_server_mod_calls(self, server_id: int):
        status_code, response_json = await self._send_request('GET', '/server/mod_calls', server_id)
        if status_code == 200:
            return [ServerModCalls(
                caller=log.get('caller'),
                moderator=log.get('moderator'),
                timestamp=log.get('timestamp')
            ) for log in response_json]
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )
        
    async def get_server_bans(self, server_id: int):
        status_code, response_json = await self._send_request('GET', '/server/bans', server_id)
        if status_code == 200:
            return [ServerBans(
                player_id=ban.get('player_id')
            ) for ban in response_json]
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )
        
    async def get_server_vehicles(self, server_id: int):
        status_code, response_json = await self._send_request('GET', '/server/vehicles', server_id)
        if status_code == 200:
            return [ServerVehicles(
                texture=vehicle.get('texture'),
                name=vehicle.get('name'),
                owner=vehicle.get('owner')
            ) for vehicle in response_json]
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )
        
    async def get_server_commands(self, server_id: int):
        status_code, response_json = await self._send_request('GET', '/server/commands', server_id)
        if status_code == 200:
            return [ServerCommand(
                command=command.get('command')
            ) for command in response_json]
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )
        
    async def send_command(self, server_id: int, command: str):
        status_code, response_json = await self._send_request('POST', '/server/command', server_id, {"command": command})
        if status_code == 200:
            return response_json
        else:
            raise ResponseFailed(
                data=response_json,
                detail=response_json.get('detail'),
                code=status_code
            )

    async def unban_player(self, server_id: int, player_id: int):
        status_code, response_json = await self._send_request('POST', '/server/command', server_id, data={
                "command": ":unban {}".format(str(player_id))
            })
        if status_code == 429:
            await asyncio.sleep(response_json['retry_after']+0.1)
            return await self.unban_player(server_id, player_id)
        if status_code == 200:
            return response_json
        
        raise ResponseFailed(
            data=response_json,
            detail=response_json.get('detail'),
            code=status_code
        )
    
    async def ban_player(self, server_id: int, player_id: int):
        status_code, response_json = await self._send_request('POST', '/server/command', server_id, data={
                "command": ":ban {}".format(str(player_id))
            })
        if status_code == 429:
            await asyncio.sleep(response_json['retry_after']+0.1)
            return await self.ban_player(server_id, player_id)
        if status_code == 200:
            return response_json
        
        raise ResponseFailed(
            data=response_json,
            detail=response_json.get('detail'),
            code=status_code
        )
    
    async def kick_player(self, server_id: int, player_id: int):
        status_code, response_json = await self._send_request('POST', '/server/command', server_id, data={
                "command": ":kick {}".format(str(player_id))
            })
        if status_code == 429:
            await asyncio.sleep(response_json['retry_after']+0.1)
            return await self.kick_player(server_id, player_id)
        if status_code == 200:
            return response_json
        
        raise ResponseFailed(
            data=response_json,
            detail=response_json.get('detail'),
            code=status_code
        )