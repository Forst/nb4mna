from dataclasses import dataclass
import logging
from typing import List

import httpx
from pydantic import BaseModel, HttpUrl

from ..caching import AsyncCachedHTTPTransport


# region Data models
class UrbanDictionaryAPIError(BaseModel):
    error: str


class AutocompletionList(BaseModel):
    list: List[str]


class TermDefinition(BaseModel):
    definition: str
    permalink: HttpUrl
    word: str


class TermDefinitions(BaseModel):
    list: List[TermDefinition]
# endregion


# region Exceptions
@dataclass
class UrbanDictionaryAPIException(Exception):
    api_error: UrbanDictionaryAPIError

    def __str__(self) -> str:
        return self.api_error.error
# endregion


class UrbanDictionaryAPI:
    API_ENDPOINT = 'https://api.urbandictionary.com/v0'

    def __init__(self) -> None:
        self._logger = logging.getLogger('nb4mna.api.urbandictionary')

        self.client = httpx.AsyncClient(
            http2=True,
            transport=AsyncCachedHTTPTransport(
                http2=True,
                cache_duration=600.0,
            ),
        )

    def _error(self, api_error: UrbanDictionaryAPIError) -> None:
        self._logger.error(f'{api_error=}', stacklevel=2)
        raise UrbanDictionaryAPIException(api_error=api_error)

    async def get_autocomplete(self, term: str) -> AutocompletionList:
        api_result = await self.client.get(f'{self.API_ENDPOINT}/autocomplete', params={'term': term})

        if api_result.status_code != httpx.codes.OK:
            api_error = UrbanDictionaryAPIError(**api_result.json())
            self._error(api_error=api_error)

        autocomplete_list = AutocompletionList(list=api_result.json())
        return autocomplete_list

    async def get_term(self, term: str) -> TermDefinitions:
        api_result = await self.client.get(f'{self.API_ENDPOINT}/define', params={'term': term})

        if api_result.status_code != httpx.codes.OK:
            api_error = UrbanDictionaryAPIError(**api_result.json())
            self._error(api_error=api_error)

        term_definitions = TermDefinitions(**api_result.json())
        return term_definitions
