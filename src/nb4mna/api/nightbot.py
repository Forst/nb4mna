import logging
from urllib.parse import parse_qs

from fastapi import Depends, Header
from pydantic import BaseModel, HttpUrl


MAX_MESSAGE_LENGTH = 400


_logger = logging.getLogger('nb4mna.api.nightbot')


# region Data models
class URLEncodedModel(BaseModel):
    def __init__(self, url_encoded: str) -> None:
        qs = parse_qs(url_encoded, keep_blank_values=True, strict_parsing=True)
        data = {key: value[0] for key, value in qs.items()}
        super().__init__(**data)


class NightbotUser(URLEncodedModel):
    name: str
    displayName: str
    provider: str
    providerId: str
    userLevel: str


class NightbotChannel(URLEncodedModel):
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
        user=NightbotUser(nightbot_user),
        channel=NightbotChannel(nightbot_channel),
    )


NightbotDepends = Depends(_dependency)
