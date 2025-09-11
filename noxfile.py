# Based on 'Hypermodern Python' article series by Claudio Jolowicz
# https://cjolowicz.github.io/posts/hypermodern-python-03-linting/

from typing import Protocol

import nox
import nox_poetry


# Default list of files to check
locations = ['src', './noxfile.py']
# List of supported Python versions (ordered newest to oldest)
supported_python_versions = ['3.13', '3.12']

nox.options.sessions = ('flake8', 'mypy', 'safety')


class TemporaryFileProtocol(Protocol):
    name: str


@nox_poetry.session(python=supported_python_versions[0])
def black(session: nox.Session) -> None:
    args = session.posargs or locations
    session.install('black')
    # TODO When 'black' addresses the '# endregion' line spacing, make this command actually clean up code
    # https://github.com/psf/black/issues/3566
    session.run('black', '--check', '--diff', '--color', *args)


@nox_poetry.session(python=supported_python_versions)
def flake8(session: nox.Session) -> None:
    args = session.posargs or locations
    session.install(
        # 'black',
        'flake8',
        'flake8-bandit',
        # 'flake8-black',
        'flake8-bugbear',
        'flake8-import-order',
        'flake8-pyproject',
    )
    session.run('flake8', *args)


@nox_poetry.session(python=supported_python_versions)
def mypy(session: nox.Session) -> None:
    args = session.posargs or locations
    session.install(
        '.',
        'mypy',
        'types-PyYAML',
        'nox',
        'nox-poetry',
    )
    session.run('mypy', *args)


@nox_poetry.session(python=supported_python_versions[0])
def safety(session: nox.Session) -> None:
    session.install('safety')
    session.run('safety', 'scan', '--detailed-output')
