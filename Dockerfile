FROM python:3.10.1-slim

COPY . /usr/src/app/
RUN pip install --no-cache-dir /usr/src/app

CMD ["python", "-m", "uvicorn", "--host", "0.0.0.0", "--no-server-header", "nb4mna:app"]

EXPOSE 8000/tcp