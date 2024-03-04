import logging
import re

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import PlainTextResponse, Response

from ...api.nightbot import MAX_MESSAGE_LENGTH
from ...api.urbandictionary import TermDefinition, UrbanDictionaryAPI, UrbanDictionaryAPIException


URBANDICTIONARY_REGEX = re.compile(r'\[(.+?)]')

router = APIRouter(prefix='/urban')

_logger = logging.getLogger('nb4mna.modules.urban')
_urbandictionary = UrbanDictionaryAPI()


@router.get('/')
async def urban(term: str) -> PlainTextResponse:
    _logger.debug(f'{term=}')

    autocomplete = await _urbandictionary.get_autocomplete(term)
    if not autocomplete.list:
        return PlainTextResponse(f'No definitions found for "{term}"')
    _logger.debug(f'Autocomplete: {autocomplete.list}')

    # Urban Dictionary's API is a hot mess
    # For example, for term "spam" it returns
    # ['Sam', 'Samantha', 'Samuel', 'SPAM', ...]
    # The exact matching term is not first, so we try to find one ourselves in the suggested list
    try:
        term_autocompleted = next(t for t in autocomplete.list if term.lower() == t.lower())
    except StopIteration:
        term_autocompleted = autocomplete.list[0]

    if term != term_autocompleted:
        _logger.debug(f"Autocompleted term '{term}' to '{term_autocompleted}'")

    terms = await _urbandictionary.get_term(term_autocompleted)
    if not terms.list:
        return PlainTextResponse(f'No definitions found for "{term}" (API bug?)')

    term_definition: TermDefinition = terms.list[0]

    word_f = f'**{term_definition.word}.** '
    url_f = f' {term_definition.permalink}'

    definition = term_definition.definition.replace('\r', '').replace('\n', ' ')
    definition = URBANDICTIONARY_REGEX.sub(r'\1', definition)

    max_definition_length = MAX_MESSAGE_LENGTH - len(word_f) - len(url_f)

    if len(definition) > max_definition_length:
        definition = definition[: max_definition_length - 1] + '…'

    return PlainTextResponse(f'{word_f}{definition}{url_f}')


def _api_exception_handler(request: Request, exc: Exception) -> Response:
    return PlainTextResponse(f'Urban Dictionary API error: {exc}')


def install(app: FastAPI) -> None:
    app.include_router(router)
    app.add_exception_handler(UrbanDictionaryAPIException, _api_exception_handler)
