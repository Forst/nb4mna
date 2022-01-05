from dataclasses import dataclass
import logging

import httpx
from pydantic import BaseModel

from ..caching import AsyncCachedHTTPTransport


# region Data models
class TatsumakiAPIError(BaseModel):
    code: int
    message: str


class MemberRanking(BaseModel):
    guild_id: int
    rank: int
    score: int
    user_id: int
# endregion


# region Exceptions
@dataclass
class TatsumakiAPIException(Exception):
    api_error: TatsumakiAPIError

    def __str__(self) -> str:
        return f'{self.api_error.message} ({self.api_error.code})'
# endregion


class TatsumakiAPI:
    API_ENDPOINT = 'https://api.tatsu.gg/v1'

    def __init__(self, api_key: str, guild_id: int) -> None:
        self._logger = logging.getLogger(f'nb4mna.api.tatsumaki.{guild_id}')

        self.client = httpx.AsyncClient(
            http2=True,
            transport=AsyncCachedHTTPTransport(
                http2=True,
                cache_duration=60.0,
            ),
        )
        self.client.headers['Authorization'] = api_key

        self.guild_id = guild_id

    def __hash__(self) -> int:
        return hash(self.guild_id)

    def _error(self, api_error: TatsumakiAPIError) -> None:
        self._logger.error(f'{api_error=}', stacklevel=2)
        raise TatsumakiAPIException(api_error=api_error)

    async def get_guild_member_ranking(self, user_id: int) -> MemberRanking:
        api_result = await self.client.get(f'{self.API_ENDPOINT}/guilds/{self.guild_id}/rankings/members/{user_id}/all')

        if api_result.status_code != httpx.codes.OK:
            api_error = TatsumakiAPIError(**api_result.json())
            self._error(api_error=api_error)

        member_ranking = MemberRanking(**api_result.json())

        if member_ranking.guild_id != self.guild_id:
            api_error = TatsumakiAPIError(code=-1, message="Guild ID doesn't match between request and response")
            self._error(api_error=api_error)

        if member_ranking.user_id != user_id:
            api_error = TatsumakiAPIError(code=-1, message="User ID doesn't match between request and response")
            self._error(api_error=api_error)

        self._logger.debug(member_ranking)
        return member_ranking
