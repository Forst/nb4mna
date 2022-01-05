__version__ = '0.1.0'


from .logging import configure_logging
configure_logging()

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from .modules import fight, urban


app = FastAPI(
    title='nb4mna',
    description='Custom Nightbot APIs for MedicNinjaa',
    version=__version__,
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(CorrelationIdMiddleware)


@app.get('/healthcheck/')
def healthcheck():
    return {'status': 'ok'}


fight.install(app)
urban.install(app)
