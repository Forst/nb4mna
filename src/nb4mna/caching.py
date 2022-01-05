import asyncio
import logging
from time import time
from typing import Any, Dict, NamedTuple

from httpx import AsyncHTTPTransport, Request, Response


class CacheKey(NamedTuple):
    method: str
    url: str

    def __str__(self) -> str:
        return f'{self.method} {self.url}'


class CacheValue(NamedTuple):
    response: Response
    time: float


class AsyncCachedHTTPTransport(AsyncHTTPTransport):
    def __init__(self, *args: Any, cache_duration: float, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._logger = logging.getLogger('nb4mna.caching')

        self.cache: Dict[CacheKey, CacheValue] = {}
        self.cache_duration = cache_duration
        self.cache_write_lock = asyncio.Lock()

        self.cache_clear_task = asyncio.create_task(self.clear_cache_task())

    @staticmethod
    def get_cache_key(request: Request) -> CacheKey:
        return CacheKey(method=request.method, url=str(request.url))

    @staticmethod
    def is_request_response_cacheable(request: Request, response: Response) -> bool:
        return request.method == 'GET' and response.status_code < 500

    async def clear_cache_task(self) -> None:
        self._logger.debug(f'Started periodic cache clearing task (every {self.cache_duration:.0f} seconds)')

        while True:
            async with self.cache_write_lock:
                now = time()
                for cache_key in list(self.cache.keys()):
                    if (now - self.cache[cache_key].time) > self.cache_duration:
                        self._logger.debug(f'{cache_key}: expired, clearing from cache')
                        self.cache.pop(cache_key)

            await asyncio.sleep(self.cache_duration)

    async def handle_async_request(self, request: Request) -> Response:
        cache_key = self.get_cache_key(request)
        cache_value = self.cache.get(cache_key, None)

        if not cache_value or time() - cache_value.time > self.cache_duration:
            self._logger.debug(f'{cache_key}: cached response unavailable or expired')
            response = await super().handle_async_request(request)

            if self.is_request_response_cacheable(request, response):
                self._logger.debug(f'{cache_key}: saving {response}')
                async with self.cache_write_lock:
                    self.cache[cache_key] = CacheValue(
                        response=response,
                        time=time(),
                    )
            else:
                self._logger.debug(f'{cache_key}: not caching, ineligible')

            return response
        else:
            self._logger.debug(f'{cache_key}: using cached {cache_value}')
            return cache_value.response
