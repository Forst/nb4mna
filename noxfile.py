# Based on 'Hypermodern Python' article series by Claudio Jolowicz
# https://cjolowicz.github.io/posts/hypermodern-python-03-linting/

from contextlib import contextmanager
import tempfile
from typing import Iterator, Protocol

import nox
import nox_poetry


# Default list of files to check
locations = ['src', './noxfile.py']
# List of supported Python versions (ordered newest to oldest)
supported_python_versions = ['3.12', '3.11', '3.10', '3.9', '3.8']

nox.options.sessions = ('flake8', 'mypy', 'safety')


class TemporaryFileProtocol(Protocol):
    name: str


@contextmanager
def requirements(session: nox.Session) -> Iterator[TemporaryFileProtocol]:
    with tempfile.NamedTemporaryFile() as requirements_file:
        session.run(
            'poetry',
            'export',
            '--with=dev',
            '--format=requirements.txt',
            '--without-hashes',
            f'--output={requirements_file.name}',
            external=True,
        )
        yield requirements_file


@nox_poetry.session(python=supported_python_versions[0])
def black(session: nox.Session) -> None:
    args = session.posargs or locations
    session.install('black')
    # TODO When 'black' addresses the '# endregion' line spacing, make this command actually clean up code
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
    with requirements(session) as requirements_file:  # type: TemporaryFileProtocol
        session.run('safety', 'check', f'--file={requirements_file.name}', '--full-report')
