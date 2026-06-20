FROM python:3.13.14-slim

COPY . /usr/src/app/
WORKDIR /usr/src/app/
RUN pip install --no-cache-dir poetry && \
    poetry install

CMD ["poetry", "run", "python", "-m", "uvicorn", "--fd", "3", "--no-server-header", "nb4mna:app"]
