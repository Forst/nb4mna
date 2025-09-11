import logging
from typing import Type, TypeVar
from urllib.parse import parse_qs

from fastapi import Depends, Header
from pydantic import BaseModel, HttpUrl


MAX_MESSAGE_LENGTH = 400


_logger = logging.getLogger('nb4mna.api.nightbot')


# region Data models
ModelT = TypeVar('ModelT')


def url_decode(model: Type[ModelT], url_encoded: str) -> ModelT:
    qs = parse_qs(url_encoded, keep_blank_values=True, strict_parsing=True)
    data = {key: value[0] for key, value in qs.items()}
    return model(**data)


class NightbotUser(BaseModel):
    name: str
    displayName: str
    provider: str
    providerId: str
    userLevel: str


class NightbotChannel(BaseModel):
    name: str
    displayName: str
    provider: str
    providerId: str


class NightbotData(BaseModel):
    response_url: HttpUrl
    user: NightbotUser
    channel: NightbotChannel
# endregion


def _dependency(
    nightbot_response_url: HttpUrl = Header(None),  # noqa: B008
    nightbot_user: str = Header(None),  # noqa: B008
    nightbot_channel: str = Header(None),  # noqa: B008
) -> NightbotData:

    _logger.debug(f'{nightbot_user=}\n{nightbot_channel=}')

    return NightbotData(
        response_url=nightbot_response_url,
        user=url_decode(NightbotUser, nightbot_user),
        channel=url_decode(NightbotChannel, nightbot_channel),
    )


NightbotDepends = Depends(_dependency)
