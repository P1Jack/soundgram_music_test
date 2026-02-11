import json
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException, status

import modules.link_parser as link_parser


def setup_logging():
    os.makedirs('logs', exist_ok=True)
    os.environ.setdefault('WATCHFILES_IGNORE_PATTERNS', 'logs/*')

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    root_logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    root_file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10_485_760,
        backupCount=5,
        encoding='utf-8'
    )
    root_file_handler.setFormatter(formatter)
    root_file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(root_file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    request_logger = logging.getLogger("request")
    request_logger.setLevel(logging.INFO)
    request_logger.propagate = False

    request_file_handler = RotatingFileHandler(
        'logs/requests.log',
        maxBytes=10_485_760,
        backupCount=5,
        encoding='utf-8'
    )
    request_file_handler.setFormatter(formatter)
    request_file_handler.setLevel(logging.INFO)
    request_logger.addHandler(request_file_handler)

    noisy_loggers = [
        "httpcore",
        "httpcore.http11",
        "httpx",
        "httpx._client",
        "watchfiles.main"
    ]

    for logger_name in noisy_loggers:
        try:
            lib_logger = logging.getLogger(logger_name)
            lib_logger.setLevel(logging.WARNING)
            lib_logger.propagate = False
            lib_logger.handlers.clear()
        except Exception as e:
            pass

    return request_logger


request_logger = setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Soundgram_YM_parser"
)


@asynccontextmanager
async def lifespan():
    logger.info("Starting FastAPI application")
    yield
    logger.info("Shutting down FastAPI application")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    try:
        response = await call_next(request)

        request_logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status: {response.status_code}"
        )

        return response
    except Exception as e:
        request_logger.error(
            f"Error: {request.method} {request.url.path} - {e}"
        )
        raise


@app.get('/')
async def root():
    return {
        "message": "TSOI ZHIV",
        "help": "Hello world! This microservice is used to parse YandexMusic playlists for future TMA "
                "interface of SoundGram! To get JSON, go to /get_playlist_info/{playlist link}"
    }


@app.get('/get_playlist_info/{playlist_link:path}')
async def get_playlist_info(playlist_link: str):
    logger.debug(f"Getting playlist info at '{playlist_link}'")

    parser_response = await link_parser.parse_link(playlist_link)
    logger.debug(f"Successfully got parser response for '{playlist_link}'")

    case = parser_response['case']

    if case == 'Successful parsing':
        json_parser_response = json.dumps(parser_response["playlist"], ensure_ascii=False, indent=4)
        return Response(
            content=json_parser_response,
            media_type="application/json; charset=utf-8"
        )

    elif case == 'Invalid link' or case == 'Empty playlist':
        status_code = status.HTTP_400_BAD_REQUEST,

    elif case == 'Playlist not found':
        status_code = status.HTTP_404_NOT_FOUND,

    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,

    raise HTTPException(
            status_code=status_code,
            detail={
                'message': parser_response['message'],
                'case': case
            }
        )
