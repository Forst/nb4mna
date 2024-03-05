FROM python:3.12.2-slim

COPY . /usr/src/app/
WORKDIR /usr/src/app/
RUN pip install --no-cache-dir poetry && \
    poetry install

CMD ["poetry", "run", "python", "-m", "uvicorn", "--host", "0.0.0.0", "--no-server-header", "nb4mna:app"]

EXPOSE 8000/tcp
