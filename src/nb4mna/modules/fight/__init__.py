from asyncio import create_task
from dataclasses import dataclass
from importlib import resources
import logging
from random import choice, randint
import re
from typing import List

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel
import yaml

from ...api.nightbot import NightbotData, NightbotDepends
from ...api.tatsumaki import TatsumakiAPI, TatsumakiAPIException
from ...settings import settings


DISCORD_USER_ID_REGEX = re.compile(r'(?<=<@)\d+(?=>)')
DISCORD_USER_ID_TEMPLATE = '<@{}>'

TWITCH_USER_ID_REGEX = re.compile(r'^@?[a-z0-9][a-z0-9_]{3,24}', re.ASCII | re.IGNORECASE)
TWITCH_USER_ID_TEMPLATE = '{}'


# region Data models
@dataclass
class FightInput:
    source_user: str
    source_probability: int
    target_user: str
    target_probability: int


class Phrases(BaseModel):
    verbs: List[str]
    weapons: List[str]
    win: List[str]
    loss: List[str]
# endregion


router = APIRouter(prefix='/fight')

_logger = logging.getLogger('nb4mna.modules.fight')
_tatsumaki = TatsumakiAPI(
    api_key=settings.tatsumaki.api_key,
    guild_id=settings.tatsumaki.guild_id,
)

with resources.open_binary(__package__, 'phrases.yaml') as f:
    phrases = Phrases(**yaml.safe_load(f))
    _logger.info(
        'Loaded'
        f' {len(phrases.verbs)} verbs,'
        f' {len(phrases.weapons)} weapons,'
        f' {len(phrases.win)} win texts,'
        f' {len(phrases.loss)} loss texts'
    )


async def fight_discord(nightbot: NightbotData, message: str) -> FightInput:
    assert nightbot.user.provider == 'discord', 'Invalid provider'  # noqa: S101

    message = message.replace('!', '')  # account for user IDs like <@!123>

    if nightbot.user.providerId:
        source_user_id = int(nightbot.user.providerId)
    else:
        raise ValueError("I don't recognise you")

    target_user_id_match = DISCORD_USER_ID_REGEX.search(message)
    if target_user_id_match:
        target_user_id = int(target_user_id_match.group(0))
    else:
        raise ValueError("You haven't specified a user to fight. You have to mention them with an @.")

    if source_user_id == target_user_id:
        source_probability = 1
        target_probability = 1
    else:
        source_probability_task = create_task(_tatsumaki.get_guild_member_ranking(source_user_id))
        target_probability_task = create_task(_tatsumaki.get_guild_member_ranking(target_user_id))
        source_probability = (await source_probability_task).score
        target_probability = (await target_probability_task).score

    return FightInput(
        source_user=DISCORD_USER_ID_TEMPLATE.format(source_user_id),
        source_probability=source_probability,
        target_user=DISCORD_USER_ID_TEMPLATE.format(target_user_id),
        target_probability=target_probability,
    )


async def fight_twitch(nightbot: NightbotData, message: str) -> FightInput:
    assert nightbot.user.provider == 'twitch', 'Invalid provider'  # noqa: S101

    source_user_id = nightbot.user.name

    target_user_id_match = TWITCH_USER_ID_REGEX.search(message)
    if target_user_id_match:
        target_user_id = target_user_id_match.group(0)
    else:
        raise ValueError("You haven't specified a user to fight.")

    return FightInput(
        source_user=TWITCH_USER_ID_TEMPLATE.format(source_user_id),
        source_probability=1,
        target_user=TWITCH_USER_ID_TEMPLATE.format(target_user_id),
        target_probability=1,
    )


@router.get('/')
async def fight(message: str, nightbot: NightbotData = NightbotDepends) -> PlainTextResponse:
    _logger.debug(f'{message[:40]=}')

    try:
        if nightbot.user.provider == 'discord':
            fight_input = await fight_discord(nightbot, message)
        elif nightbot.user.provider == 'twitch':
            fight_input = await fight_twitch(nightbot, message)
        else:
            raise ValueError('Unsupported provider')
    except ValueError as e:
        _logger.error(e)
        return PlainTextResponse(str(e))

    _logger.info(
        f'{fight_input.source_user=} {fight_input.source_probability=}'
        f' {fight_input.target_user=} {fight_input.target_probability=}'
    )

    if fight_input.source_user == fight_input.target_user:
        return PlainTextResponse(
            f'{fight_input.source_user} fought with themselves and are now in a state of quantum superposition.'
        )

    if fight_input.source_probability == 0:
        return PlainTextResponse(
            f"{fight_input.source_user}, you're not in the leaderboard just yet,"
            " get some more XP and try fighting again later."
        )

    if fight_input.target_probability == 0:
        return PlainTextResponse(
            f"{fight_input.source_user}, you can't fight somebody with no experience at all. Shame on you!"
        )

    result = randint(1, fight_input.source_probability + fight_input.target_probability)
    probability = fight_input.source_probability / (fight_input.source_probability + fight_input.target_probability)
    is_win = 1 <= result <= fight_input.source_probability

    verb = choice(phrases.verbs)
    weapon = choice(phrases.weapons)
    conclusion = choice(phrases.win) + '!' if is_win else choice(phrases.loss) + '.'

    _logger.info(f'{result=} {is_win=}')

    return PlainTextResponse(
        f'{fight_input.source_user} {verb} {fight_input.target_user}'
        f' with {weapon} and {conclusion}'
        f' ({probability:.01%} win chance)'
    )


def _api_exception_handler(request: Request, exc: Exception) -> Response:
    return PlainTextResponse(f'Tatsumaki API error: {exc}')


def install(app: FastAPI) -> None:
    app.include_router(router)
    app.add_exception_handler(TatsumakiAPIException, _api_exception_handler)
