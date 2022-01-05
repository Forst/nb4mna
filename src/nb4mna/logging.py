from logging.config import dictConfig

from asgi_correlation_id.log_filters import correlation_id_filter


def configure_logging() -> None:
    dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'filters': {
                'correlation_id': {'()': correlation_id_filter(8)},
            },
            'formatters': {
                'console': {
                    'class': 'logging.Formatter',
                    'format': (
                        '%(levelname)3s:\t%(asctime)s [%(correlation_id)s] %(name)s'
                        ' %(filename)s:%(lineno)d %(funcName)s(): %(message)s'
                    ),
                },
                'console_brief': {
                    'class': 'logging.Formatter',
                    'format': '%(levelname)3s:\t%(asctime)s [%(correlation_id)s] %(name)s: %(message)s',
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'filters': ['correlation_id'],
                    'formatter': 'console',
                },
                'console_brief': {
                    'class': 'logging.StreamHandler',
                    'filters': ['correlation_id'],
                    'formatter': 'console_brief',
                },
            },
            'loggers': {
                'nb4mna': {'handlers': ['console_brief'], 'level': 'DEBUG'},
                'httpx': {'handlers': ['console_brief'], 'level': 'DEBUG'},
                'uvicorn': {'handlers': ['console_brief'], 'level': 'INFO'},
            },
        }
    )
