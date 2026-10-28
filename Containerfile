FROM python:3.15.2-slim

WORKDIR /usr/src/app/

COPY pyproject.toml poetry.lock /usr/src/app/
WORKDIR /usr/src/app/
RUN pip install --no-cache-dir poetry && \
    poetry install --no-root

COPY . /usr/src/app/
RUN poetry install

CMD ["poetry", "run", "python", "-m", "uvicorn", "--fd", "3", "--no-server-header", "nb4mna:app"]
